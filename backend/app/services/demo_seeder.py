import sqlite3
import json
import uuid
from pathlib import Path
from app.config import MEDIA_DIR
from app.database import get_db_connection
from app.services.audio_generator import generate_audio_lesson
from app.services.video_generator import generate_video_lesson

def seed_demo_data(generate_media_assets: bool = True):
    """
    Seeds complete, world-class sample courses with pre-rendered diagrams, audio, and video
    so the app runs instantly out of the box in under 60 seconds!
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) as cnt FROM books")
    row = cursor.fetchone()
    if row and row["cnt"] > 0:
        conn.close()
        return

    print("Seeding Book2Course AI demonstration library...")

    sample_books = [
        {
            "id": "book-lean-startup",
            "title": "The Lean Startup",
            "author": "Eric Ries",
            "pages": 336,
            "cover_color": "#0A66C2", # LinkedIn Blue
            "summary": "How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses.",
            "course": {
                "id": "course-lean-startup",
                "title": "Mastering The Lean Startup Methodology",
                "subtitle": "Build-Measure-Learn Feedback Loops, Minimum Viable Products, and Validated Learning",
                "overview": "Eric Ries defines a startup as a human institution designed to create something new under conditions of extreme uncertainty. This course translates the scientific approach of validated learning into immediate execution.",
                "target_audience": "Founders, Product Managers, Innovation Leads, Engineers",
                "levels": [
                    {
                        "id": "lvl-ls-1",
                        "level_number": 1,
                        "title": "Level 1: Vision & Validated Learning",
                        "description": "Stop wasting time building products nobody wants. Validate your leap-of-faith assumptions first.",
                        "lessons": [
                            {
                                "id": "lsn-ls-1",
                                "title": "The Core Feedback Loop: Build-Measure-Learn",
                                "short_summary": "The fundamental engine of startup growth is the speed at which you traverse the Build-Measure-Learn loop.",
                                "long_explanation": "Rather than executing an elaborate multi-year business plan into thin air, successful ventures treat every product decision as an experiment. The goal of a startup is not to see how many features can be coded, but how quickly you can learn what customers actually desire and are willing to pay for.",
                                "key_ideas": [
                                    "Start with learning milestones, not vanity delivery dates.",
                                    "Minimize total cycle time through the Build-Measure-Learn loop.",
                                    "Treat every feature hypothesis as a testable scientific statement."
                                ],
                                "practical_insights": [
                                    "Define what metric constitutes validation before shipping an experiment.",
                                    "Measure customer actions instead of surveying hypothetical opinions.",
                                    "Ship small batch updates rather than large monolith releases."
                                ],
                                "examples": [
                                    "Dropbox launching with a simple 3-minute explainer video that generated 75,000 signups overnight.",
                                    "Zappos founder Nick Swinmurn photographing shoes at local stores before buying any inventory."
                                ],
                                "action_items": [
                                    "Formulate your primary hypothesis in a single testable sentence.",
                                    "Identify the smallest experiment capable of testing this hypothesis.",
                                    "Set a timebox of 7 days to gather real customer behavioural data."
                                ],
                                "mermaid_diagram": """graph TD
    Ideas["1. Ideas & Hypotheses"] --> Build["2. BUILD (Code/Prototype)"]
    Build --> Product["3. Product / Experiment"]
    Product --> Measure["4. MEASURE (Metrics)"]
    Measure --> Data["5. Quantitative Data"]
    Data --> Learn["6. LEARN (Validated Insights)"]
    Learn --> Pivot{"Pivot or Persevere?"}
    Pivot -->|Persevere| Ideas
    Pivot -->|Pivot| Vision["Revise Strategy"]
    Vision --> Ideas
    style Ideas fill:#0A66C2,color:#FFF
    style Build fill:#378FE9,color:#FFF
    style Product fill:#57A3FF,color:#191919
    style Measure fill:#EBF3FA,color:#191919
    style Data fill:#CBD5E1,color:#191919
    style Learn fill:#057642,color:#FFF
    style Pivot fill:#D97706,color:#FFF"""
                            },
                            {
                                "id": "lsn-ls-2",
                                "title": "The Minimum Viable Product (MVP) Blueprint",
                                "short_summary": "An MVP is that version of a new product which allows a team to collect the maximum amount of validated learning with the least effort.",
                                "long_explanation": "An MVP is not a broken, poor-quality product; it is a razor-sharp tool designed to test specific business hypotheses. Any feature or perfectionism beyond what is strictly necessary to begin learning is a form of waste.",
                                "key_ideas": [
                                    "Remove any feature, process, or design element that does not directly contribute to learning.",
                                    "Use concierge or Wizard of Oz MVPs to validate demand before writing code.",
                                    "Embrace early adopters who forgive initial rough edges in exchange for solving a painful problem."
                                ],
                                "practical_insights": [
                                    "Test willingness to pay as early as possible.",
                                    "Don't hide behind nondisclosure agreements; customer feedback is what gives ideas value.",
                                    "Measure engagement retention curves over simple signup counts."
                                ],
                                "examples": [
                                    "Food on the Table starting with zero software, serving a single customer manually in grocery aisles.",
                                    "Buffer creating a 2-page pricing landing page to verify credit card click intentions before writing the scheduler."
                                ],
                                "action_items": [
                                    "List all current planned features and cut 50% that aren't critical to your core value hypothesis.",
                                    "Draft a landing page test with a clear call-to-action.",
                                    "Interview 5 potential early adopters to uncover their current workarounds."
                                ],
                                "mermaid_diagram": """graph LR
    Hypothesis["Core Value Hypothesis"] --> LowCode["Concierge / Wizard of Oz MVP"]
    LowCode --> EarlyAdopters["Early Adopter Feedback"]
    EarlyAdopters --> Quantitative["Retention & Referral Proof"]
    Quantitative --> Scale["Automate & Scale"]
    style Hypothesis fill:#0A66C2,color:#FFF
    style LowCode fill:#378FE9,color:#FFF
    style EarlyAdopters fill:#EBF3FA,color:#191919
    style Quantitative fill:#57A3FF,color:#191919
    style Scale fill:#057642,color:#FFF"""
                            }
                        ]
                    },
                    {
                        "id": "lvl-ls-2",
                        "level_number": 2,
                        "title": "Level 2: Steering & Innovation Accounting",
                        "description": "Distinguish between actionable metrics and deceptive vanity metrics to make data-backed pivot decisions.",
                        "lessons": [
                            {
                                "id": "lsn-ls-3",
                                "title": "Actionable Metrics vs. Vanity Metrics",
                                "short_summary": "Vanity metrics make you feel good but do not reflect real business health. Actionable metrics demonstrate cause and effect.",
                                "long_explanation": "Total registered users or page views will almost always trend upwards as long as you spend money on marketing. However, cohort retention, activation rates, and viral coefficient give you the undeniable truth about product-market fit.",
                                "key_ideas": [
                                    "The 3 A's of metrics: Actionable, Accessible, and Auditable.",
                                    "Use cohort analysis to compare how new customer groups behave versus older ones.",
                                    "Never confuse raw traffic with customer validation."
                                ],
                                "practical_insights": [
                                    "Track Week-1, Week-4, and Month-3 retention curves.",
                                    "Make metrics visible to the entire development squad on a public dashboard.",
                                    "Tie every new experiment to a specific metric delta."
                                ],
                                "examples": [
                                    "IMVU learning that their 3D chat avatar customers preferred using chat with their existing friends, not meeting strangers.",
                                    "Grooveshark pivoting based on playlist sharing viral loops rather than sheer banner impressions."
                                ],
                                "action_items": [
                                    "Audit your company dashboard and archive 3 vanity metrics.",
                                    "Implement cohort tracking for your latest user signup flow.",
                                    "Conduct a split A/B test on your primary activation screen."
                                ],
                                "mermaid_diagram": """graph TD
    Subscribers["Total Signups (Vanity)"] -.-> FalseConfidence["False Sense of Success"]
    Cohorts["Cohort Retention (Actionable)"] --> Reality["True Product-Market Fit"]
    Reality --> Experimentation["Targeted Improvements"]
    Experimentation --> Growth["Sustainable Scaled Engine"]
    style Subscribers fill:#EF4444,color:#FFF
    style FalseConfidence fill:#F87171,color:#FFF
    style Cohorts fill:#0A66C2,color:#FFF
    style Reality fill:#378FE9,color:#FFF
    style Experimentation fill:#57A3FF,color:#191919
    style Growth fill:#057642,color:#FFF"""
                            },
                            {
                                "id": "lsn-ls-4",
                                "title": "The Art of the Pivot: Strategic Course Correction",
                                "short_summary": "A pivot is a structured course correction designed to test a new fundamental hypothesis about the product, business model, or engine of growth.",
                                "long_explanation": "Pivot is not an admission of failure; it is keeping one foot firmly anchored in what you have learned while shifting the other foot into a more lucrative direction. Startups that run out of money fail because they run out of pivots.",
                                "key_ideas": [
                                    "Hold regular 'Pivot or Persevere' meetings every 4 to 6 weeks.",
                                    "Zoom-In Pivot: Refocusing on a single compelling feature that customers adore.",
                                    "Customer Segment Pivot: Keeping the product but targeting an audience with higher willingness to pay."
                                ],
                                "practical_insights": [
                                    "Do not delay pivots out of sunk cost fallacy.",
                                    "Treat every pivot as a hypothesis that must be validated within 30 days.",
                                    "Communicate pivot rationale transparently to your investors and team."
                                ],
                                "examples": [
                                    "Instagram starting as Burbn, a cluttered location check-in app, and zooming in purely on photos and filters.",
                                    "Slack starting as an internal chat tool inside a failed gaming venture called Glitch."
                                ],
                                "action_items": [
                                    "Schedule a monthly Pivot-or-Persevere review with leadership.",
                                    "Analyze user feature telemetry to locate your hidden 'zoom-in' runaway feature.",
                                    "Calculate your startup runway in terms of 'Pivots Remaining'."
                                ],
                                "mermaid_diagram": """graph LR
    DataCheck["Review Cohort Signals"] --> Evaluation{"Growth Plateaued?"}
    Evaluation -->|Yes| PivotChoice["Select Pivot Strategy: Zoom-In / Segment / Channel"]
    Evaluation -->|No| DoubleDown["Persevere & Optimize Funnel"]
    PivotChoice --> FreshLoop["Initiate New Build-Measure-Learn Loop"]
    style DataCheck fill:#0A66C2,color:#FFF
    style Evaluation fill:#D97706,color:#FFF
    style PivotChoice fill:#378FE9,color:#FFF
    style DoubleDown fill:#057642,color:#FFF
    style FreshLoop fill:#0A66C2,color:#FFF"""
                            }
                        ]
                    },
                    {
                        "id": "lvl-ls-3",
                        "level_number": 3,
                        "title": "Level 3: Acceleration & Engines of Growth",
                        "description": "Scale through the 3 Engines of Growth and implement the Five Whys to eliminate systemic defects.",
                        "lessons": [
                            {
                                "id": "lsn-ls-5",
                                "title": "The Three Engines of Growth",
                                "short_summary": "Sustainable growth follows one of three engines: Sticky, Viral, or Paid. Focus relentlessly on one.",
                                "long_explanation": "Startups often stumble trying to optimize all growth mechanisms simultaneously. The Sticky engine focuses on ultra-low churn; the Viral engine relies on referral loops and coefficients greater than 1.0; the Paid engine scales when Customer Lifetime Value exceeds Cost of Acquisition by at least 3x.",
                                "key_ideas": [
                                    "Sticky Engine: Retaining existing customers compounds recurring revenue.",
                                    "Viral Engine: Product usage inherently exposes the product to prospective new users.",
                                    "Paid Engine: Reinvesting marginal gross profit into scalable acquisition channels."
                                ],
                                "practical_insights": [
                                    "Pick only ONE primary engine of growth at a time.",
                                    "For viral growth, reduce friction in the invite or share flow to zero.",
                                    "For paid growth, measure payback period in months."
                                ],
                                "examples": [
                                    "Hotmail attaching 'P.S. Get your free email at Hotmail' to every outgoing email.",
                                    "eBay benefiting from sticky network effects where buyers attracted sellers and vice versa."
                                ],
                                "action_items": [
                                    "Classify your current product into its primary growth engine.",
                                    "Measure your viral coefficient (k-factor) or churn rate.",
                                    "Eliminate paid marketing spend if your LTV is less than 3x CAC."
                                ],
                                "mermaid_diagram": """graph TD
    Engines["Engines of Growth"] --> Sticky["1. Sticky Engine (Low Churn)"]
    Engines --> Viral["2. Viral Engine (k > 1.0)"]
    Engines --> Paid["3. Paid Engine (LTV > 3x CAC)"]
    Sticky --> Compounding["High Retention Compounding"]
    Viral --> Organic["Exponential Network Growth"]
    Paid --> Reinvestment["Profitable Reinvestment Cycle"]
    style Engines fill:#0A66C2,color:#FFF
    style Sticky fill:#378FE9,color:#FFF
    style Viral fill:#57A3FF,color:#191919
    style Paid fill:#057642,color:#FFF"""
                            },
                            {
                                "id": "lsn-ls-6",
                                "title": "The Five Whys: Root Cause Problem Solving",
                                "short_summary": "When technical or human failures arise, ask 'Why?' five times to identify the root cause and build proportional preventive investments.",
                                "long_explanation": "Behind every seemingly technical problem is a human problem. The Five Whys method ties rate of progress to institutional learning. When a server goes down or a critical bug ships, rather than pointing fingers, the team diagnoses systemic failure and invests proportionally to fix the underlying process.",
                                "key_ideas": [
                                    "Ask 'Why?' five consecutive times to trace back to human training and process gaps.",
                                    "Make proportional investments at every level of the Five Whys chain.",
                                    "Foster a blameless culture focused on fixing systems, not punishing individuals."
                                ],
                                "practical_insights": [
                                    "Hold Five Whys meetings with all affected team members within 24 hours of an outage.",
                                    "Assign clear owners and deadlines to the preventive action items.",
                                    "Start with small proportional investments to avoid bureaucratic gridlock."
                                ],
                                "examples": [
                                    "A failed server deployment leading to discovering the absence of automated staging test scripts.",
                                    "Toyota resolving machine breakdowns by discovering clogged lubrication strainers."
                                ],
                                "action_items": [
                                    "Conduct a 5 Whys retrospective on the latest customer escalation.",
                                    "Implement an automated test or checklist for the root cause found.",
                                    "Commit to blameless operational retrospectives."
                                ],
                                "mermaid_diagram": """graph TD
    Symptom["Symptom: Server Crash"] --> W1["Why 1: Out of Memory Exception"]
    W1 --> W2["Why 2: Cache was not evicted"]
    W2 --> W3["Why 3: Missing eviction configuration"]
    W3 --> W4["Why 4: Developer was unfamiliar with service"]
    W4 --> W5["Why 5: No onboarding checklist for production configs"]
    W5 --> Prevention["Fix: Automated Onboarding Verification"]
    style Symptom fill:#EF4444,color:#FFF
    style W1 fill:#F87171,color:#FFF
    style W2 fill:#FBBF24,color:#191919
    style W3 fill:#378FE9,color:#FFF
    style W4 fill:#0A66C2,color:#FFF
    style W5 fill:#057642,color:#FFF
    style Prevention fill:#10B981,color:#FFF"""
                            }
                        ]
                    }
                ],
                "flashcards": [
                    {
                        "question": "What is the primary definition of a startup according to Eric Ries?",
                        "answer": "A human institution designed to deliver a new product or service under conditions of extreme uncertainty.",
                        "category": "Foundations"
                    },
                    {
                        "question": "What is the core purpose of a Minimum Viable Product (MVP)?",
                        "answer": "To collect the maximum amount of validated learning about customers with the least development effort.",
                        "category": "Product Development"
                    },
                    {
                        "question": "What are the three steps in the core Lean Startup feedback loop?",
                        "answer": "Build -> Measure -> Learn (repeated continuously at maximum cycle speed).",
                        "category": "Methodology"
                    },
                    {
                        "question": "What is a 'Vanity Metric'?",
                        "answer": "A metric (like raw page views or total signups) that increases regardless of whether the business is healthy or retaining users.",
                        "category": "Metrics"
                    },
                    {
                        "question": "What are the three A's of actionable metrics?",
                        "answer": "Actionable, Accessible, and Auditable.",
                        "category": "Metrics"
                    },
                    {
                        "question": "What constitutes a 'Zoom-In Pivot'?",
                        "answer": "Refocusing an entire product around a single high-performing feature that customers love.",
                        "category": "Strategy"
                    },
                    {
                        "question": "What are the Three Engines of Growth?",
                        "answer": "The Sticky Engine, the Viral Engine, and the Paid Engine.",
                        "category": "Growth"
                    },
                    {
                        "question": "What must the viral coefficient (k) be for exponential organic viral growth?",
                        "answer": "Greater than 1.0 (meaning each user successfully recruits more than one additional user).",
                        "category": "Growth"
                    },
                    {
                        "question": "What is the purpose of the 'Five Whys' methodology?",
                        "answer": "To identify the root human and process causes behind technical failures and make proportional preventive investments.",
                        "category": "Operations"
                    },
                    {
                        "question": "Why is validated learning superior to shipping features on time?",
                        "answer": "Because building a product on time that nobody wants is 100% waste.",
                        "category": "Mindset"
                    },
                    {
                        "question": "What is a Concierge MVP?",
                        "answer": "An MVP where the service is provided completely manually to early adopters to observe their real needs before coding.",
                        "category": "Prototyping"
                    },
                    {
                        "question": "What is Innovation Accounting?",
                        "answer": "A quantitative framework to establish a baseline, tune the engine, and decide whether to pivot or persevere objectively.",
                        "category": "Finance & Strategy"
                    }
                ],
                "quizzes": [
                    {
                        "question": "Which of the following is the true objective of a Minimum Viable Product (MVP)?",
                        "options": [
                            "To ship a buggy prototype to prove you can code fast",
                            "To begin the process of validated learning as quickly as possible",
                            "To earn maximum revenue on day one",
                            "To replace all future design and engineering work"
                        ],
                        "correct_index": 1,
                        "explanation": "The MVP is specifically engineered to test core value hypotheses with minimal effort and accelerate learning."
                    },
                    {
                        "question": "Why are cohort metrics vastly superior to cumulative totals?",
                        "options": [
                            "They look more impressive on investor decks",
                            "They isolate the behavior of specific customer segments over time to reveal genuine retention",
                            "They require fewer data scientists to calculate",
                            "They always show positive growth numbers"
                        ],
                        "correct_index": 1,
                        "explanation": "Cohorts expose whether newer product iterations are truly retaining users or if churn is disguised by raw acquisition."
                    },
                    {
                        "question": "If your startup's primary engine is the Viral Engine, what metric is most vital?",
                        "options": [
                            "Customer Acquisition Cost (CAC)",
                            "Viral Coefficient (k-factor > 1.0)",
                            "Monthly Recurring Revenue (MRR)",
                            "Total Press Mentions"
                        ],
                        "correct_index": 1,
                        "explanation": "If each new user brings in more than 1 additional user (k > 1), the product achieves self-sustaining exponential growth."
                    },
                    {
                        "question": "When should an executive or founder declare a pivot?",
                        "options": [
                            "Every time an individual user complains about a minor button color",
                            "When experiments demonstrate the current engine cannot achieve sustainable business milestones",
                            "Only after 100% of cash reserves are exhausted",
                            "Never, because pivoting signifies total defeat"
                        ],
                        "correct_index": 1,
                        "explanation": "Pivots are disciplined strategic shifts made when empirical cohort data shows the current hypothesis has hit a ceiling."
                    },
                    {
                        "question": "What does Eric Ries identify as the primary cause of waste in modern ventures?",
                        "options": [
                            "Inefficient server architectures",
                            "Building features and products that nobody actually wants",
                            "Spending too much money on coffee",
                            "Failing to file patents immediately"
                        ],
                        "correct_index": 1,
                        "explanation": "The greatest form of waste is executing with supreme efficiency something that should never have been built at all."
                    },
                    {
                        "question": "What is the key rule during a 'Five Whys' retrospective?",
                        "options": [
                            "Find the individual employee at fault and administer a disciplinary reprimand",
                            "Keep asking why until an external third party is blamed",
                            "Uncover systemic process failures and make proportional preventive investments blamelessly",
                            "Stop asking after the second question if it seems uncomfortable"
                        ],
                        "correct_index": 2,
                        "explanation": "The Five Whys method is designed to diagnose systemic and training deficiencies without human blame."
                    }
                ]
            }
        },
        {
            "id": "book-atomic-habits",
            "title": "Atomic Habits",
            "author": "James Clear",
            "pages": 320,
            "cover_color": "#057642", # LinkedIn / Success Green
            "summary": "An Easy & Proven Way to Build Good Habits & Break Bad Ones.",
            "course": {
                "id": "course-atomic-habits",
                "title": "Atomic Habits: The Complete Behavioral Mastery Course",
                "subtitle": "The 4 Laws of Behavior Change, Identity-Based Systems, and 1% Compounding",
                "overview": "James Clear illustrates that real change comes from the compound effect of hundreds of small decisions. You do not rise to the level of your goals; you fall to the level of your systems.",
                "target_audience": "Professionals, Leaders, Students, Anyone seeking permanent personal and career transformation",
                "levels": [
                    {
                        "id": "lvl-ah-1",
                        "level_number": 1,
                        "title": "Level 1: Fundamentals of Atomic Habits",
                        "description": "Understand the mathematical power of 1% gains and shift your focus from outcomes to identity.",
                        "lessons": [
                            {
                                "id": "lsn-ah-1",
                                "title": "The Surprising Power of 1% Compounding",
                                "short_summary": "Improving by 1% every day for a year yields a 37x compound improvement by day 365.",
                                "long_explanation": "Habits are the compound interest of self-improvement. Getting 1 percent better each day counts for a lot in the long run. If you can get 1 percent better each day for one year, you’ll end up thirty-seven times better by the time you’re done.",
                                "key_ideas": [
                                    "1% better every day = 37.78x over 365 days.",
                                    "Breakthrough moments are often the result of many previous actions building up latent potential.",
                                    "Goals set direction; systems build continuous progress."
                                ],
                                "practical_insights": [
                                    "Focus on trajectories over current position.",
                                    "Do not judge results on days 1 through 30; wait for compounding to emerge.",
                                    "Measure system adherence rather than daily outcome spikes."
                                ],
                                "examples": [
                                    "Dave Brailsford transforming the British Cycling team by improving bike seats, tires, and sleeping mattresses by 1%.",
                                    "An author writing just 250 words a day producing a 90,000-word book every single year."
                                ],
                                "action_items": [
                                    "Identify one tiny 1% upgrade in your daily morning ritual.",
                                    "Commit to 14 days of unbroken consistency.",
                                    "Write down the trajectory of your current habits over 5 years."
                                ],
                                "mermaid_diagram": """graph LR
    Day1["Day 1: 1.00"] --> Day90["Day 90: 2.45"]
    Day90 --> Day180["Day 180: 6.00"]
    Day180 --> Day365["Day 365: 37.78x"]
    style Day1 fill:#64748B,color:#FFF
    style Day90 fill:#378FE9,color:#FFF
    style Day180 fill:#0A66C2,color:#FFF
    style Day365 fill:#057642,color:#FFF"""
                            },
                            {
                                "id": "lsn-ah-2",
                                "title": "Identity-Based Habits: Changing Who You Are",
                                "short_summary": "The ultimate form of intrinsic motivation is when a habit becomes part of your identity.",
                                "long_explanation": "Behind every system of actions is a system of beliefs. Most people try to change their habits by focusing on what they want to achieve (outcomes). The alternative is to build identity-based habits: decide who you want to be, then prove it to yourself with small wins.",
                                "key_ideas": [
                                    "Three layers of behavior change: Outcome -> Process -> Identity.",
                                    "Every action you take is a vote for the type of person you wish to become.",
                                    "True behavior change is identity change."
                                ],
                                "practical_insights": [
                                    "Ask yourself: 'What would a healthy/productive person do in this situation?'",
                                    "Cast small votes daily rather than seeking overnight transformations.",
                                    "Reframe 'I have to do this' into 'I get to do this because of who I am'."
                                ],
                                "examples": [
                                    "A person turning down a cigarette by declaring 'No thanks, I'm not a smoker' versus 'No thanks, I'm trying to quit'.",
                                    "A programmer who commits code daily because 'I am a builder who crafts software'."
                                ],
                                "action_items": [
                                    "Write down the identity statement: 'I am the type of person who...'",
                                    "Cast 2 votes for this identity today with tangible actions.",
                                    "Identify an old limiting self-belief and deliberately rewrite it."
                                ],
                                "mermaid_diagram": """graph TD
    Identity["Identity: Who you want to be"] --> Process["Process: What you do daily"]
    Process --> Outcome["Outcome: What you achieve"]
    style Identity fill:#057642,color:#FFF
    style Process fill:#0A66C2,color:#FFF
    style Outcome fill:#378FE9,color:#FFF"""
                            }
                        ]
                    },
                    {
                        "id": "lvl-ah-2",
                        "level_number": 2,
                        "title": "Level 2: The 4 Laws of Behavior Change",
                        "description": "Master the habit loop: Cue, Craving, Response, and Reward to build good habits and dismantle bad ones.",
                        "lessons": [
                            {
                                "id": "lsn-ah-3",
                                "title": "The 1st & 2nd Laws: Make It Obvious & Attractive",
                                "short_summary": "Engineer your cues into plain sight and pair desired actions with immediate anticipation.",
                                "long_explanation": "The human brain is a prediction machine. Environment design is the secret weapon: by placing visual cues directly in your path, productive habits require zero activation memory. Pairing an action you need to do with an action you want to do (Temptation Bundling) makes it irresistible.",
                                "key_ideas": [
                                    "1st Law: Make it Obvious. Redesign your environment to make cues unmistakable.",
                                    "Habit Stacking: 'After [Current Habit], I will [New Habit]'.",
                                    "2nd Law: Make it Attractive. Dopamine drives desire and anticipation."
                                ],
                                "practical_insights": [
                                    "Leave a water bottle and notebook on your desk before going to sleep.",
                                    "Only listen to your favorite podcast while doing cardio workouts.",
                                    "Join a culture where your desired behavior is the normal behavior."
                                ],
                                "examples": [
                                    "A hospital cafeteria increasing water sales by 25% simply by placing bottled water baskets beside every cash register.",
                                    "An engineer pairing coffee brewing with writing the day's top 3 priorities."
                                ],
                                "action_items": [
                                    "Design a 1-sentence Habit Stack for your morning.",
                                    "Place a physical cue for your primary habit where you cannot miss it.",
                                    "Pair a chore with your favorite entertainment."
                                ],
                                "mermaid_diagram": """graph LR
    Cue["1. Cue: Make it Obvious"] --> Craving["2. Craving: Make it Attractive"]
    Craving --> Response["3. Response: Make it Easy"]
    Response --> Reward["4. Reward: Make it Satisfying"]
    style Cue fill:#0A66C2,color:#FFF
    style Craving fill:#378FE9,color:#FFF
    style Response fill:#57A3FF,color:#191919
    style Reward fill:#057642,color:#FFF"""
                            },
                            {
                                "id": "lsn-ah-4",
                                "title": "The 3rd & 4th Laws: Make It Easy & Satisfying",
                                "short_summary": "Reduce friction to initiate action and attach immediate positive reinforcement.",
                                "long_explanation": "Human nature naturally follows the Law of Least Effort. To build a new habit, downscale it until it takes less than 2 minutes to perform (The Two-Minute Rule). To sustain it, ensure the immediate outcome is satisfying, because behaviors that are immediately rewarded get repeated.",
                                "key_ideas": [
                                    "3rd Law: Make it Easy. Reduce friction and activation energy.",
                                    "The Two-Minute Rule: When you start a new habit, it should take less than two minutes.",
                                    "4th Law: Make it Satisfying. Immediate reinforcement cements neurological pathways."
                                ],
                                "practical_insights": [
                                    "Scale down reading a chapter into 'Read just 1 page'.",
                                    "Scale down going to the gym into 'Put on my workout shoes and step outside'.",
                                    "Use a visual habit tracker; don't break the chain."
                                ],
                                "examples": [
                                    "A reader reading 1 page every night who eventually read 30 books a year.",
                                    "A software developer using automated test badges as an immediate satisfying reward."
                                ],
                                "action_items": [
                                    "Shrink your hardest habit down to a 2-minute version.",
                                    "Create a physical checkbox or habit tracker calendar.",
                                    "Celebrate immediately upon finishing your 2-minute ritual."
                                ],
                                "mermaid_diagram": """graph TD
    Goal["Big Goal: 60-Minute Workout"] --> Rule2Min["Two-Minute Rule: Put on Shoes & Stretch"]
    Rule2Min --> Gateway["Gateway Habit Established"]
    Gateway --> FullRoutine["Effortless Full Routine Flow"]
    style Goal fill:#64748B,color:#FFF
    style Rule2Min fill:#0A66C2,color:#FFF
    style Gateway fill:#378FE9,color:#FFF
    style FullRoutine fill:#057642,color:#FFF"""
                            }
                        ]
                    },
                    {
                        "id": "lvl-ah-3",
                        "level_number": 3,
                        "title": "Level 3: Advanced Tactics & Habit Mastery",
                        "description": "Maintain consistency across years, leverage habit contracts, and adhere to the Goldilocks Rule.",
                        "lessons": [
                            {
                                "id": "lsn-ah-5",
                                "title": "The Goldilocks Rule & Overcoming Boredom",
                                "short_summary": "Humans experience peak motivation when working on tasks right on the edge of current ability.",
                                "long_explanation": "The greatest threat to success is not failure but boredom. Anyone can work hard when they feel motivated; it's the ability to keep going when work is not exciting that makes the difference.",
                                "key_ideas": [
                                    "The Goldilocks Rule: 4% beyond your current comfort zone.",
                                    "Professionals stick to the schedule; amateurs let life get in the way.",
                                    "Fall in love with boredom and routine consistency."
                                ],
                                "practical_insights": [
                                    "Adjust difficulty dynamically so tasks are neither too simple nor crushing.",
                                    "Keep showing up even when you can only give 60%.",
                                    "Establish an accountability partner or habit contract."
                                ],
                                "examples": [
                                    "Elite Olympic athletes training with the exact same drills for decades without complaining of repetition.",
                                    "Chess grandmasters playing opponents slightly higher rated to spark flow state."
                                ],
                                "action_items": [
                                    "Calibrate your current main task to be 4% more challenging.",
                                    "Sign an accountability pact with a colleague.",
                                    "Acknowledge when boredom strikes as the exact moment separation happens."
                                ],
                                "mermaid_diagram": """graph LR
    Boredom["Too Easy = Boredom"] --> Flow["Peak Motivation: 4% Edge (Goldilocks Zone)"]
    Flow --> Anxiety["Too Hard = Anxiety / Quitting"]
    style Boredom fill:#CBD5E1,color:#191919
    style Flow fill:#057642,color:#FFF
    style Anxiety fill:#EF4444,color:#FFF"""
                            },
                            {
                                "id": "lsn-ah-6",
                                "title": "The Rule of Never Missing Twice",
                                "short_summary": "Missing once is an accident. Missing twice is the start of a new habit.",
                                "long_explanation": "Perfection is impossible; life will inevitably disrupt your routine. What separates winners from perpetual quitters is how they respond to the missed rep. By committing to never miss twice, you preserve the underlying system regardless of circumstances.",
                                "key_ideas": [
                                    "The first mistake is never the one that ruins you; it is the spiral of repeated mistakes.",
                                    "Always show up for a 'bad' workout or a short 5-minute study block.",
                                    "Slumps are broken by immediate micro-actions, not waiting for next week."
                                ],
                                "practical_insights": [
                                    "If you miss your workout, do 10 pushups immediately.",
                                    "If you eat poorly at lunch, eat a disciplined dinner that same evening.",
                                    "Never allow a bad day to turn into a bad week."
                                ],
                                "examples": [
                                    "Jerry Seinfeld's 'Don't Break the Chain' comedy writing calendar.",
                                    "Stephen King writing 2,000 words every day of the year including holidays."
                                ],
                                "action_items": [
                                    "Re-establish any habit you dropped this week right now.",
                                    "Write 'Never Miss Twice' where you see it daily.",
                                    "Complete your final course quiz and receive your certification."
                                ],
                                "mermaid_diagram": """graph TD
    Slip["Isolated Miss (Accident)"] --> Choice{"Response Today"}
    Choice -->|Resume Immediately| Momentum["System Preserved & Reinforced"]
    Choice -->|Miss Again| NewHabit["New Bad Habit Solidified"]
    style Slip fill:#FBBF24,color:#191919
    style Momentum fill:#057642,color:#FFF
    style NewHabit fill:#EF4444,color:#FFF"""
                            }
                        ]
                    }
                ],
                "flashcards": [
                    {
                        "question": "What is an 'Atomic Habit'?",
                        "answer": "A tiny regular practice or routine that is not only small and easy to do, but also the source of immense compound power.",
                        "category": "Foundations"
                    },
                    {
                        "question": "What are the four stages of the habit loop?",
                        "answer": "1. Cue, 2. Craving, 3. Response, 4. Reward.",
                        "category": "Habit Loop"
                    },
                    {
                        "question": "What is the formula for Habit Stacking?",
                        "answer": "After [CURRENT HABIT], I will [NEW HABIT].",
                        "category": "Tactics"
                    },
                    {
                        "question": "What is the Two-Minute Rule for habit formation?",
                        "answer": "When you start a new habit, scale it down so that it takes less than two minutes to perform.",
                        "category": "Execution"
                    },
                    {
                        "question": "Why is identity-based change more powerful than outcome-based change?",
                        "answer": "Because the focus is on who you wish to become rather than merely what you wish to achieve.",
                        "category": "Psychology"
                    },
                    {
                        "question": "What does the 1st Law of Behavior Change dictate?",
                        "answer": "Make it Obvious (engineer your environment to make cues impossible to miss).",
                        "category": "The 4 Laws"
                    },
                    {
                        "question": "What does the 2nd Law of Behavior Change dictate?",
                        "answer": "Make it Attractive (pair habits with anticipation and dopamine rewards).",
                        "category": "The 4 Laws"
                    },
                    {
                        "question": "What does the 3rd Law of Behavior Change dictate?",
                        "answer": "Make it Easy (reduce the activation energy and friction to start).",
                        "category": "The 4 Laws"
                    },
                    {
                        "question": "What does the 4th Law of Behavior Change dictate?",
                        "answer": "Make it Satisfying (give yourself an immediate, tangible reward).",
                        "category": "The 4 Laws"
                    },
                    {
                        "question": "What is the 'Goldilocks Rule' of motivation?",
                        "answer": "Humans experience peak motivation when working on tasks right at the edge of their current abilities (~4% difficulty boost).",
                        "category": "Mastery"
                    },
                    {
                        "question": "What is the 'Never Miss Twice' principle?",
                        "answer": "An isolated slip is an accident; missing twice is the beginning of an unwanted new habit.",
                        "category": "Resilience"
                    },
                    {
                        "question": "What is Temptation Bundling?",
                        "answer": "Linking an action you want to do with an action you need to do.",
                        "category": "Tactics"
                    }
                ],
                "quizzes": [
                    {
                        "question": "According to James Clear, what happens when you improve by 1% each day for a year?",
                        "options": [
                            "You become exactly 3.65x better",
                            "You become nearly 38 times (37.78x) better",
                            "You burn out completely",
                            "Nothing perceptible changes"
                        ],
                        "correct_index": 1,
                        "explanation": "Compounding interest (1.01^365) means micro-gains multiply into massive results over time."
                    },
                    {
                        "question": "Which of the following is an example of an identity-based statement?",
                        "options": [
                            "I want to run a marathon by November",
                            "I am a runner who embraces physical training",
                            "I hope to lose 10 pounds this summer",
                            "My goal is to read 20 books"
                        ],
                        "correct_index": 1,
                        "explanation": "Identity statements define who you are rather than external goals you seek to acquire."
                    },
                    {
                        "question": "What is the primary function of the Two-Minute Rule?",
                        "options": [
                            "To finish your entire workout in 120 seconds",
                            "To master the art of showing up by establishing a gateway ritual",
                            "To replace all complex learning with micro-skits",
                            "To ensure you never spend more than two minutes on any project"
                        ],
                        "correct_index": 1,
                        "explanation": "A habit must be established before it can be improved; the two-minute rule makes starting effortless."
                    },
                    {
                        "question": "If you want to break a bad habit, what is the inverse of the 1st Law (Make it Obvious)?",
                        "options": [
                            "Make it Invisible (remove the cue from your environment)",
                            "Make it Painful",
                            "Make it Complicated",
                            "Make it Boring"
                        ],
                        "correct_index": 0,
                        "explanation": "Removing the visual cue breaks the habit loop before craving and impulse are triggered."
                    },
                    {
                        "question": "Why does the British Cycling team serve as a prime case study in Atomic Habits?",
                        "options": [
                            "They purchased the most expensive bikes in the world",
                            "They aggregated hundreds of marginal 1% gains across every operational aspect",
                            "They trained 24 hours a day without sleeping",
                            "They relied solely on natural genetic advantages"
                        ],
                        "correct_index": 1,
                        "explanation": "Dave Brailsford's strategy of the aggregation of marginal gains produced unprecedented Olympic and Tour de France dominance."
                    },
                    {
                        "question": "What is the core philosophy regarding goals vs systems in Atomic Habits?",
                        "options": [
                            "Winners have goals; losers do not have goals",
                            "You do not rise to the level of your goals; you fall to the level of your systems",
                            "Goals are completely useless and should never be formulated",
                            "Systems only matter once goals are already achieved"
                        ],
                        "correct_index": 1,
                        "explanation": "Both winners and losers share identical goals; systems are what determine who consistently executes."
                    }
                ]
            }
        }
    ]

    for b in sample_books:
        # Insert book
        cursor.execute("""
        INSERT INTO books (id, title, author, page_count, cover_color, summary, status)
        VALUES (?, ?, ?, ?, ?, ?, 'ready')
        """, (b["id"], b["title"], b["author"], b["pages"], b["cover_color"], b["summary"]))

        c = b["course"]
        total_lessons = sum(len(lvl["lessons"]) for lvl in c["levels"])
        total_quizzes = len(c["quizzes"])
        total_cards = len(c["flashcards"])

        cursor.execute("""
        INSERT INTO courses (id, book_id, title, subtitle, overview, target_audience, estimated_duration, level_count, lesson_count, quiz_count, flashcard_count)
        VALUES (?, ?, ?, ?, ?, ?, '15 mins', ?, ?, ?, ?)
        """, (c["id"], b["id"], c["title"], c["subtitle"], c["overview"], c["target_audience"], len(c["levels"]), total_lessons, total_quizzes, total_cards))

        for lvl in c["levels"]:
            cursor.execute("""
            INSERT INTO levels (id, course_id, level_number, title, description)
            VALUES (?, ?, ?, ?, ?)
            """, (lvl["id"], c["id"], lvl["level_number"], lvl["title"], lvl["description"]))

            for lsn_idx, lsn in enumerate(lvl["lessons"]):
                # Audio generation
                audio_url = f"/media/audio/{lsn['id']}.mp3"
                video_url = f"/media/video/{lsn['id']}.mp4"

                if generate_media_assets:
                    try:
                        audio_url = generate_audio_lesson(
                            lesson_id=lsn["id"],
                            title=lsn["title"],
                            summary=lsn["short_summary"],
                            key_ideas=lsn["key_ideas"],
                            examples=lsn["examples"],
                            conclusion="Implement these steps directly into your daily routine."
                        )
                    except Exception as e:
                        print(f"Demo audio warning: {e}")

                    try:
                        video_url = generate_video_lesson(
                            lesson_id=lsn["id"],
                            lesson_title=lsn["title"],
                            course_title=c["title"],
                            summary=lsn["short_summary"],
                            key_ideas=lsn["key_ideas"],
                            examples=lsn["examples"],
                            action_items=lsn["action_items"],
                            audio_path=audio_url
                        )
                    except Exception as e:
                        print(f"Demo video warning: {e}")

                transcript_scenes = [
                    {"scene": 1, "title": "Introduction", "timestamp": "0:00", "speaker": f"Welcome to {lsn['title']}."},
                    {"scene": 2, "title": "Core Summary", "timestamp": "0:04", "speaker": lsn['short_summary']},
                    {"scene": 3, "title": "Main Principles", "timestamp": "0:08", "speaker": ". ".join(lsn['key_ideas'][:2])},
                    {"scene": 4, "title": "Framework Diagram", "timestamp": "0:12", "speaker": "Notice how the structural loop connects inputs directly to outputs."},
                    {"scene": 5, "title": "Practical Application", "timestamp": "0:16", "speaker": lsn['examples'][0] if lsn['examples'] else ""},
                    {"scene": 6, "title": "Conclusion & Action", "timestamp": "0:20", "speaker": "Take action on these steps and proceed to the next module."}
                ]

                cursor.execute("""
                INSERT INTO lessons (id, course_id, level_id, order_index, title, short_summary, long_explanation, key_ideas, practical_insights, examples, action_items, mermaid_diagram, audio_url, video_url, transcript, duration, completed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2 mins', 0)
                """, (
                    lsn["id"],
                    c["id"],
                    lvl["id"],
                    lsn.get("order_index", lsn_idx + 1),
                    lsn["title"],
                    lsn["short_summary"],
                    lsn["long_explanation"],
                    json.dumps(lsn["key_ideas"]),
                    json.dumps(lsn["practical_insights"]),
                    json.dumps(lsn["examples"]),
                    json.dumps(lsn["action_items"]),
                    lsn["mermaid_diagram"],
                    audio_url,
                    video_url,
                    json.dumps(transcript_scenes)
                ))

        # Flashcards
        for card in c["flashcards"]:
            card_id = f"fc-{uuid.uuid4().hex[:8]}"
            cursor.execute("""
            INSERT INTO flashcards (id, course_id, question, answer, category, mastered)
            VALUES (?, ?, ?, ?, ?, 0)
            """, (card_id, c["id"], card["question"], card["answer"], card["category"]))

        # Quizzes
        for q in c["quizzes"]:
            q_id = f"qz-{uuid.uuid4().hex[:8]}"
            cursor.execute("""
            INSERT INTO quizzes (id, course_id, question, options, correct_index, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (q_id, c["id"], q["question"], json.dumps(q["options"]), q["correct_index"], q["explanation"]))

    conn.commit()
    conn.close()
    print("Demo library seeded successfully with 2 comprehensive books, courses, audio, and videos!")
