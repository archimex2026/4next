"""Authored study samples, added without modifying existing personal materials."""
import json
from contextlib import closing
from app.database import get_db_connection
from app.services.ai_analyzer import build_content_aware_curriculum

SAMPLES = [
    ("biologie", "Biologie · energia din lumea vie", "ro", "#DCE7D6", """Celula și energia

Celula este unitatea structurală și funcțională a organismelor vii. Membrana celulară delimitează celula și controlează schimburile de substanțe cu mediul. Citoplasma reprezintă mediul în care au loc numeroase reacții chimice. În celulele eucariote, nucleul conține cea mai mare parte a materialului genetic.

Fotosinteza este procesul prin care plantele transformă energia luminoasă în energie chimică. La plante, fotosinteza are loc în cloroplaste. Clorofila absoarbe lumina, iar energia captată susține formarea substanțelor organice. Plantele folosesc dioxid de carbon și apă pentru a produce glucoză și oxigen. Oxigenul rezultat poate fi eliberat în atmosferă. Lumina, temperatura și disponibilitatea apei influențează desfășurarea fotosintezei.

Respirația celulară eliberează energia din substanțele organice, făcând-o disponibilă proceselor celulare. În respirația aerobă, glucoza reacționează cu oxigenul, rezultând dioxid de carbon, apă și energie. O parte din energia eliberată este transferată în molecule de ATP. La celulele eucariote, mitocondriile au un rol important în respirația aerobă. Plantele realizează atât fotosinteză, cât și respirație celulară.

Într-un ecosistem, producătorii formează substanțe organice pornind de la substanțe anorganice. Consumatorii obțin substanțe organice hrănindu-se cu alte organisme sau cu produse ale acestora. Descompunătorii contribuie la transformarea resturilor organice și la reciclarea materiei. Energia trece între nivelurile trofice, iar o parte se disipă sub formă de căldură. Materia poate fi reciclată în ecosistem, în timp ce energia are un flux direcționat.

Compară fotosinteza cu respirația aerobă: identifică substanțele de intrare, produșii și rolul energetic al fiecărui proces. Explică de ce o plantă are nevoie și de respirație celulară. Acest material demonstrativ este o introducere de studiu, nu o programă oficială de examen."""),
    ("physics", "Physics · motion, forces and energy", "en", "#E5DFEC", """Describing motion

Displacement describes the change in an object's position and includes direction. Average velocity equals displacement divided by elapsed time. Average speed equals total distance divided by elapsed time. Acceleration describes the rate of change of velocity. An object can accelerate by changing its speed, its direction, or both.

Newton's first law states that an object maintains a constant velocity unless acted upon by a nonzero net force. Newton's second law relates net force, mass and acceleration: net force equals mass multiplied by acceleration for an object of constant mass. Force is measured in newtons. Newton's third law states that interacting objects exert forces of equal magnitude and opposite direction on each other. These two forces act on different objects.

For a constant force parallel to displacement, work equals the force multiplied by displacement. Kinetic energy is the energy associated with motion. For a body of mass m moving at speed v, kinetic energy equals one half of m multiplied by v squared. Near Earth's surface, the change in gravitational potential energy equals mass multiplied by gravitational acceleration and the change in height.

Energy can be transferred or transformed, while the total energy of an isolated system remains constant. Without friction and other dissipative effects, the sum of kinetic and potential energy remains constant. Friction can transfer mechanical energy into internal energy. Power is the rate at which work is done or energy is transferred. The SI unit of energy is the joule, and the SI unit of power is the watt.

Explain how an object moving in a circle at constant speed can be accelerating. Identify which object each force acts on in a pair of interaction forces. This authored demonstration is a starting point for revision and does not claim alignment with an official exam syllabus."""),
]


def seed_demo_data(generate_media_assets: bool = False):
    # ponytail: deterministic samples; media is requested explicitly, never on startup.
    with closing(get_db_connection()) as conn:
        for slug, title, language, color, text in SAMPLES:
            book_id, course_id = "book-demo-" + slug, "course-demo-" + slug
            if conn.execute("SELECT 1 FROM books WHERE id=?", (book_id,)).fetchone():
                continue
            pages = [{"page": 1, "text": text}]
            data = build_content_aware_curriculum(title, "Echipa 4Next", text, language=language, source_pages=pages)
            lessons = [lesson for level in data["levels"] for lesson in level["lessons"]]
            conn.execute("""INSERT INTO books(id,title,author,page_count,file_type,cover_color,status,
                owner_id,visibility,source_text,source_pages,keywords,language,study_minutes,depth,generation_mode)
                VALUES(?,?,?,1,'txt',?,'ready',NULL,'public',?,?,?,?,20,'standard','extractive')""",
                (book_id,title,"Echipa 4Next · material demonstrativ",color,text,json.dumps(pages,ensure_ascii=False),
                 json.dumps(data.get("keywords",[]),ensure_ascii=False),language))
            conn.execute("""INSERT INTO courses(id,book_id,title,subtitle,overview,target_audience,
                estimated_duration,level_count,lesson_count,quiz_count,flashcard_count,language)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (course_id,book_id,title,data.get("subtitle",""),data.get("overview",""),
                data.get("target_audience",""),data.get("estimated_duration","20 min"),len(data["levels"]),len(lessons),
                len(data.get("quizzes",[])),len(data.get("flashcards",[])),language))
            for index, level in enumerate(data["levels"]):
                level_id = f"{course_id}-level-{index}"
                conn.execute("INSERT INTO levels(id,course_id,level_number,title,description) VALUES(?,?,?,?,?)",
                    (level_id,course_id,index+1,level["title"],level.get("description","")))
                for lesson_index, lesson in enumerate(level["lessons"]):
                    fields = ["key_ideas","practical_insights","examples","action_items"]
                    conn.execute("""INSERT INTO lessons(id,course_id,level_id,order_index,title,short_summary,
                        long_explanation,key_ideas,practical_insights,examples,action_items,mermaid_diagram,
                        source_citations,transcript,duration) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'[]',?)""",
                        (f"{level_id}-lesson-{lesson_index}",course_id,level_id,index*100+lesson_index,
                         lesson["title"],lesson.get("short_summary",""),lesson.get("long_explanation",""),
                         *[json.dumps(lesson.get(f,[]),ensure_ascii=False) for f in fields],lesson.get("mermaid_diagram",""),
                         json.dumps(lesson.get("source_citations",[]),ensure_ascii=False),lesson.get("duration","5 min")))
            for index, card in enumerate(data.get("flashcards",[])):
                conn.execute("""INSERT INTO flashcards(id,course_id,question,answer,category,source_citations)
                    VALUES(?,?,?,?,?,?)""", (f"{course_id}-card-{index}",course_id,card["question"],card["answer"],
                    card.get("category",""),json.dumps(card.get("source_citations",[]),ensure_ascii=False)))
            for index, question in enumerate(data.get("quizzes",[])):
                conn.execute("""INSERT INTO quizzes(id,course_id,question,options,correct_index,explanation,source_citations)
                    VALUES(?,?,?,?,?,?,?)""", (f"{course_id}-quiz-{index}",course_id,question["question"],
                    json.dumps(question["options"],ensure_ascii=False),question["correct_index"],question.get("explanation",""),
                    json.dumps(question.get("source_citations",[]),ensure_ascii=False)))
        conn.commit()
