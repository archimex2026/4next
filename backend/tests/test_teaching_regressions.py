"""Regressions from the C++ document report; no paid calls or private PDFs in CI."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.ai_analyzer import analyze_book_with_gemini, build_content_aware_curriculum, study_context
from app.services.extractor import extract_document
from app.services.study_ai import answer_from_source, verify_citations

TEXT = ("A variable stores a value of a particular type. The type determines the operations that can be used. "
        "A constant cannot be assigned a different value after initialization. Loops repeat a statement while a condition holds.")


class TeachingRegressions(unittest.TestCase):
    def test_unavailable_verifier_does_not_spend_another_generation_attempt(self):
        course = build_content_aware_curriculum('Programming', '', TEXT, 'en')
        with patch('app.services.ai_analyzer.gemini_json', return_value=course) as generator, \
             patch('app.services.study_ai.gemini_json', return_value=None):
            result = asyncio.run(analyze_book_with_gemini('Programming', '', TEXT, 'en'))
        self.assertEqual(result['generation_mode'], 'extractive')
        generator.assert_called_once()

    def test_cited_but_semantically_invalid_teaching_requires_a_corrected_response(self):
        import copy
        course = build_content_aware_curriculum('Programming', '', TEXT, 'en')
        bad = copy.deepcopy(course)
        bad['levels'][0]['lessons'][0]['long_explanation'] = 'C++ always requires camelCase variable names and explicitly written types.'
        reason = 'A course convention cannot be taught as a universal language requirement.'
        with patch('app.services.ai_analyzer.gemini_json', side_effect=[bad, course]) as generator, \
             patch('app.services.study_ai.gemini_json', side_effect=[
                 {'supported': True, 'semantically_valid': False, 'rejection_reasons': [reason]},
                 {'supported': True, 'semantically_valid': True}]):
            result = asyncio.run(analyze_book_with_gemini('Programming', '', TEXT, 'en'))
        self.assertEqual(result['generation_mode'], 'ai_grounded')
        self.assertNotIn('always requires', result['levels'][0]['lessons'][0]['long_explanation'])
        self.assertEqual(generator.call_count, 2)
        self.assertEqual(generator.call_args.args[1]['verification_feedback'], [reason])

    def test_missing_semantic_verdict_is_rejected_even_if_citations_are_supported(self):
        from app.services.study_ai import verify_teaching
        item = {'answer': 'A variable stores a typed value.', 'source_citations': [{'page': 1, 'text': TEXT}]}
        with patch('app.services.study_ai.gemini_json', return_value={'supported': True}):
            self.assertFalse(asyncio.run(verify_teaching([item], 'en')))

    def test_short_slide_abbreviation_does_not_sever_its_explanation(self):
        from app.services.study_ai import source_fragments
        slide = 'Compiled languages\nC++ is a compiled language (vs.\ninterpreted languages such as Python). The compiler produces an executable.'
        self.assertEqual(list(source_fragments([{'page': 7, 'text': slide}])), [{'page': 7, 'text': slide}])

    def test_malformed_optional_practice_does_not_discard_a_valid_lesson(self):
        course = build_content_aware_curriculum('Programming', '', TEXT, 'en')
        course['quizzes'].append({'question': 'This incomplete question must be omitted.'})
        with patch('app.services.ai_analyzer.gemini_json', return_value=course), \
             patch('app.services.study_ai.gemini_json', return_value={'supported': True, 'semantically_valid': True}):
            result = asyncio.run(analyze_book_with_gemini('Programming', '', TEXT, 'en'))
        self.assertEqual(result['generation_mode'], 'ai_grounded')
        self.assertTrue(result['levels'][0]['lessons'])
        self.assertEqual(len(result['quizzes']), len(course['quizzes'])-1)

    def test_pdf_columns_keep_code_and_commentary_in_separate_text_blocks(self):
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Courier', size=10)
        # PDF objects are written by column; their visual rows overlap.
        for index, line in enumerate(['int value = 5;', 'value *= 2;', 'return value;']):
            pdf.text(10, 25 + index*8, line)
        for index, line in enumerate(['The parameter is a copy.', 'Changing it leaves the caller unchanged.', 'This is pass by value.']):
            pdf.text(95, 25 + index*8, line)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'columns.pdf'
            pdf.output(str(path))
            source = extract_document(path, 'pdf')['text']
        self.assertLess(source.index('return value;'), source.index('The parameter is a copy.'))
        self.assertIn('int value = 5;\nvalue *= 2;\nreturn value;', source)

    def test_ambiguous_quiz_can_be_omitted_without_losing_valid_explanations(self):
        from app.services.study_ai import verify_teaching
        course = build_content_aware_curriculum('Programming', '', TEXT, 'en')
        course['quizzes'][0]['question'] = 'What happens if you try to change the type of a variable in C++?'
        count = sum(len(level['lessons']) for level in course['levels']) + len(course['flashcards'])
        with patch('app.services.ai_analyzer.gemini_json', return_value=course), \
             patch('app.services.study_ai.gemini_json', return_value={'supported': True, 'semantically_valid': True, 'remove_practice': [count]}):
            result = asyncio.run(analyze_book_with_gemini('Programming', '', TEXT, 'en'))
        self.assertEqual(result['generation_mode'], 'ai_grounded')
        self.assertFalse(any(q['question'].startswith('What happens') for q in result['quizzes']))
        lesson = {'long_explanation': 'A variable stores a typed value.', 'source_citations': [{'page': 1, 'text': TEXT}]}
        with patch('app.services.study_ai.gemini_json', return_value={'supported': True, 'semantically_valid': True, 'remove_practice': [0]}):
            self.assertFalse(asyncio.run(verify_teaching([lesson], 'en')))

    def test_numbers_on_an_unrelated_page_do_not_validate_an_invented_claim(self):
        from app.services.study_ai import verify_teaching
        items = [{'answer': 'A variable stores 99 values.', 'source_citations': [{'page': 1, 'text': TEXT}]}]
        evidence = [{'page': 1, 'text': TEXT}, {'page': 2, 'text': 'This unrelated example uses the number 99.'}]
        with patch('app.services.study_ai.gemini_json') as provider:
            self.assertFalse(asyncio.run(verify_teaching(items, 'en', evidence)))
            provider.assert_not_called()

    def test_pdf_faux_bold_deduplicates_glyphs_without_breaking_cpp_operators(self):
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Courier', size=12)
        line = 'Vector::Vector(int s) { ++s; cout << s; }'
        pdf.text(10, 20, line)
        pdf.text(10.1, 20, line)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bold.pdf'
            pdf.output(str(path))
            source = extract_document(path, 'pdf')
        self.assertIn(line, source['text'])
        self.assertNotIn('VVeeccttoorr', source['text'])

    def test_five_minute_overview_cites_beginning_middle_and_end(self):
        pages = [{'page': i, 'text': TEXT + f' This is source section {i}.'} for i in range(1, 23)]
        course = build_content_aware_curriculum('Programming', '', '\n'.join(p['text'] for p in pages), 'en', pages, 5)
        cited = {c['page'] for l in course['levels'][0]['lessons'] for c in l['source_citations']}
        self.assertIn(1, cited)
        self.assertIn(22, cited)
        self.assertTrue(any(7 < p < 17 for p in cited))

    def test_large_documents_are_not_excluded_from_the_ai_path(self):
        pages = [{'page': i, 'text': TEXT * 50} for i in range(1, 23)]
        context = study_context(pages)
        self.assertEqual({p['page'] for p in context}, set(range(1, 23)))
        self.assertLessEqual(sum(len(p['text']) for p in context), 75000)
        with patch('app.services.ai_analyzer.gemini_json', return_value=None) as provider:
            asyncio.run(analyze_book_with_gemini('Programming', '', TEXT * 1000, 'en', pages))
        provider.assert_called_once()
        self.assertEqual({p['page'] for p in provider.call_args.args[1]['source_pages']}, set(range(1, 23)))

    def test_teacher_explanation_survives_validation_instead_of_being_replaced_by_quotes(self):
        course = build_content_aware_curriculum('Programming', '', TEXT, 'en')
        explanation = 'Start by choosing a type for your variable. This choice tells you which operations you can perform on the value it stores.'
        course['levels'][0]['lessons'][0]['long_explanation'] = explanation
        with patch('app.services.ai_analyzer.gemini_json', return_value=course), \
             patch('app.services.study_ai.gemini_json', return_value={'supported': True, 'semantically_valid': True}):
            result = asyncio.run(analyze_book_with_gemini('Programming', '', TEXT, 'en'))
        self.assertEqual(result['generation_mode'], 'ai_grounded')
        self.assertEqual(result['levels'][0]['lessons'][0]['long_explanation'], explanation)
        with patch('app.services.ai_analyzer.gemini_json', return_value=course), \
             patch('app.services.study_ai.gemini_json', return_value={'supported': False}):
            rejected = asyncio.run(analyze_book_with_gemini('Programming', '', TEXT, 'en'))
        self.assertEqual(rejected['generation_mode'], 'extractive')

    def test_general_document_question_is_answered_and_explanation_is_preserved(self):
        quote = {'page': 1, 'text': TEXT[:TEXT.index('.') + 1]}
        explanation = 'The document introduces variables, types, constants and loops. It explains how types affect the operations you can perform.'
        async def provider(task, payload, language, **kwargs):
            if 'Verify the proposed teaching' in task:
                return {'supported': True, 'semantically_valid': True}
            return {'answerable': True, 'answer': explanation, 'source_citations': [quote]}
        with patch('app.services.study_ai.gemini_json', side_effect=provider):
            result = asyncio.run(answer_from_source('what does this material contain', [{'page': 1, 'text': TEXT}], 'en', 'Programming'))
        self.assertEqual(result['answer'], explanation)
        self.assertEqual(result['mode'], 'ai_grounded')

    def test_line_wrap_normalization_returns_exact_original_citation(self):
        source = 'A constant cannot be assigned\na different value after initialization.'
        quote = {'page': 2, 'text': source.replace('\n', ' ')}
        self.assertEqual(verify_citations([quote], [{'page': 2, 'text': source}])[0]['text'], source)

    def test_citation_id_resolves_to_server_evidence_and_real_page(self):
        evidence = [{'source_id': 'e1', 'page': 7, 'text': TEXT}]
        result = verify_citations([{'source_id': 'e1', 'page': 99, 'text': 'Do not trust model quotes'}], evidence, evidence)
        self.assertEqual(result, [{'page': 7, 'text': TEXT}])
        with self.assertRaises(ValueError):
            verify_citations([{'source_id': 'invented', 'page': 7}], evidence, evidence)

    def test_bad_optional_card_is_omitted_without_discarding_valid_lessons(self):
        course = build_content_aware_curriculum('Programming', '', TEXT, 'en')
        course['flashcards'][0]['source_citations'] = [{'page': 999, 'text': 'This quote is fabricated and must never appear.'}]
        with patch('app.services.ai_analyzer.gemini_json', return_value=course), \
             patch('app.services.study_ai.gemini_json', return_value={'supported': True, 'semantically_valid': True}):
            result = asyncio.run(analyze_book_with_gemini('Programming', '', TEXT, 'en'))
        self.assertEqual(result['generation_mode'], 'ai_grounded')
        self.assertTrue(result['levels'][0]['lessons'])
        self.assertFalse(any(c['page'] == 999 for card in result['flashcards'] for c in card['source_citations']))

    def test_comparison_retrieves_pdf_kerned_identifiers(self):
        from app.services.study_ai import _retrieve
        pages = [{'page': 7, 'text': 'The const keyword promises not to change a value. A conste xpr value is evaluated at compile time.'}]
        ranked = _retrieve('What is the difference between const and constexpr?', pages)
        self.assertTrue(ranked)
        self.assertGreaterEqual(ranked[0][0], .5)

    def test_evidence_review_omits_reversed_key_idea_without_replacing_valid_explanation(self):
        from app.services.study_ai import verify_teaching
        item = {'long_explanation': 'A variable stores a typed value.',
                'key_ideas': ['Variables store values.', 'Source code is not portable.'],
                'source_citations': [{'page': 1, 'text': TEXT}]}
        with patch('app.services.study_ai.gemini_json', return_value={'supported': True, 'semantically_valid': True, 'remove_key_ideas': [{'item': 0, 'index': 1}]}):
            self.assertTrue(asyncio.run(verify_teaching([item], 'en')))
        self.assertEqual(item['key_ideas'], ['Variables store values.'])
        self.assertEqual(item['long_explanation'], 'A variable stores a typed value.')

    def test_verifier_failover_only_retries_unavailability_not_negative_verdicts(self):
        from app.services.study_ai import verify_teaching
        item = {'answer': 'A variable stores a typed value.', 'source_citations': [{'page': 1, 'text': TEXT}]}
        with patch('app.services.study_ai.gemini_json', side_effect=[None, {'supported': True, 'semantically_valid': True}]) as provider:
            self.assertTrue(asyncio.run(verify_teaching([item], 'en')))
            self.assertEqual(provider.call_count, 2)
            self.assertEqual(provider.call_args.kwargs['model'], 'gemini-3.6-flash')
        with patch('app.services.study_ai.gemini_json', return_value={'supported': False}) as provider:
            self.assertFalse(asyncio.run(verify_teaching([item], 'en')))
            provider.assert_called_once()
