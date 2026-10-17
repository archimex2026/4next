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
             patch('app.services.study_ai.gemini_json', return_value={'supported': True}):
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
        async def provider(task, payload, language):
            if 'Verify the proposed teaching' in task:
                return {'supported': True}
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

    def test_comparison_retrieves_pdf_kerned_identifiers(self):
        from app.services.study_ai import _retrieve
        pages = [{'page': 7, 'text': 'The const keyword promises not to change a value. A conste xpr value is evaluated at compile time.'}]
        ranked = _retrieve('What is the difference between const and constexpr?', pages)
        self.assertTrue(ranked)
        self.assertGreaterEqual(ranked[0][0], .5)
