import { Course, Lesson, Flashcard, QuizQuestion } from './types';

export const DEMO_COURSE: Course = {
  id: 'course-lean-startup',
  book_id: 'book-lean-startup',
  title: 'The Lean Startup: Fast Experimentation & MVPs',
  subtitle: 'Build-Measure-Learn Feedback Loops, Minimum Viable Products, and Validated Learning',
  overview: 'Eric Ries defines a startup as a human institution designed to create something new under conditions of extreme uncertainty. This course translates the scientific approach of validated learning into immediate execution.',
  author: 'Eric Ries',
  target_audience: 'Founders, Product Managers, Innovation Leads, Engineers',
  estimated_duration: '15 mins',
  completion_percentage: 33,
  level_count: 3,
  lesson_count: 6,
  flashcard_count: 12,
  quiz_count: 6,
  book: {
    id: 'book-lean-startup',
    title: 'The Lean Startup',
    author: 'Eric Ries',
    page_count: 336,
    status: 'ready',
    cover_color: '#0A66C2',
  },
  levels: [
    {
      id: 'lvl-ls-1',
      course_id: 'course-lean-startup',
      level_number: 1,
      title: 'Level 1: Vision & Validated Learning',
      description: 'Stop wasting time building products nobody wants. Validate your leap-of-faith assumptions first.',
      lessons: [
        {
          id: 'lsn-ls-1',
          course_id: 'course-lean-startup',
          level_id: 'lvl-ls-1',
          order_index: 1,
          title: 'The Core Feedback Loop: Build-Measure-Learn',
          short_summary: 'The fundamental engine of startup growth is the speed at which you traverse the Build-Measure-Learn loop.',
          long_explanation: `Rather than executing an elaborate multi-year business plan into thin air, successful ventures treat every product decision as an experiment. The goal of a startup is not to see how many features can be coded, but how quickly you can learn what customers actually desire and are willing to pay for.

True entrepreneurial efficiency comes from eliminating waste. By running micro-experiments on real cohorts, you minimize the capital and calendar days required to achieve product-market fit.`,
          key_ideas: [
            'Start with learning milestones, not vanity delivery dates.',
            'Minimize total cycle time through the Build-Measure-Learn loop.',
            'Treat every feature hypothesis as a testable scientific statement.'
          ],
          practical_insights: [
            'Define what metric constitutes validation before shipping an experiment.',
            'Measure customer actions instead of surveying hypothetical opinions.',
            'Ship small batch updates rather than large monolith releases.'
          ],
          examples: [
            'Dropbox launching with a simple 3-minute explainer video that generated 75,000 signups overnight.',
            'Zappos founder Nick Swinmurn photographing shoes at local stores before buying any inventory.'
          ],
          action_items: [
            'Formulate your primary hypothesis in a single testable sentence.',
            'Identify the smallest experiment capable of testing this hypothesis.',
            'Set a timebox of 7 days to gather real customer behavioural data.'
          ],
          mermaid_diagram: `graph TD
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
    style Pivot fill:#D97706,color:#FFF`,
          duration: '2m 30s',
          video_url: '/media/videos/lsn-ls-1.mp4',
          audio_url: '/media/audio/lsn-ls-1.mp3',
          completed: true,
          transcript: [
            { scene: 1, title: 'Introduction', timestamp: '0:00', speaker: 'Welcome to Lesson 1: The Build-Measure-Learn Feedback Loop.' },
            { scene: 2, title: 'The Lean Core', timestamp: '0:04', speaker: 'The fundamental engine of entrepreneurial growth is learning speed.' },
            { scene: 3, title: 'Loop Phases', timestamp: '0:08', speaker: 'Plan what to learn, build the smallest test, and measure action.' },
            { scene: 4, title: 'System Architecture', timestamp: '0:12', speaker: 'Review the iterative cycle diagram to align sprint goals.' },
            { scene: 5, title: 'Real-World Proof', timestamp: '0:16', speaker: 'Dropbox and Zappos validated millions in demand with zero initial code.' },
            { scene: 6, title: 'Action Plan', timestamp: '0:20', speaker: 'Timebox your primary customer hypothesis into a 7-day test.' }
          ]
        },
        {
          id: 'lsn-ls-2',
          course_id: 'course-lean-startup',
          level_id: 'lvl-ls-1',
          order_index: 2,
          title: 'The Minimum Viable Product (MVP) Blueprint',
          short_summary: 'An MVP is that version of a new product which allows a team to collect the maximum amount of validated learning with the least effort.',
          long_explanation: `An MVP is not a broken, poor-quality product; it is a razor-sharp tool designed to test specific business hypotheses. Any feature or perfectionism beyond what is strictly necessary to begin learning is a form of waste.

Entrepreneurs frequently fall into the trap of over-building before testing core willingness to pay. Using concierge tests or landing page pre-sales protects your runway while revealing genuine intent.`,
          key_ideas: [
            'Remove any feature or design element that does not directly contribute to learning.',
            'Use concierge or Wizard of Oz MVPs to validate demand before writing code.',
            'Embrace early adopters who forgive initial rough edges in exchange for solving a painful problem.'
          ],
          practical_insights: [
            'Test willingness to pay as early as possible.',
            'Do not hide behind non-disclosure agreements; feedback is what gives ideas value.',
            'Measure engagement retention curves over simple signup counts.'
          ],
          examples: [
            'Food on the Table serving a single customer manually in grocery aisles before creating an algorithm.',
            'Buffer creating a 2-page pricing landing page to verify credit card click intentions.'
          ],
          action_items: [
            'List all current planned features and cut 50% that aren’t critical to your core value hypothesis.',
            'Draft a landing page test with a clear call-to-action.',
            'Interview 5 potential early adopters to uncover their current workarounds.'
          ],
          mermaid_diagram: `graph LR
    Hypothesis["Core Value Hypothesis"] --> LowCode["Concierge / Wizard of Oz MVP"]
    LowCode --> EarlyAdopters["Early Adopter Feedback"]
    EarlyAdopters --> Quantitative["Retention & Referral Proof"]
    Quantitative --> Scale["Automate & Scale"]
    style Hypothesis fill:#0A66C2,color:#FFF
    style LowCode fill:#378FE9,color:#FFF
    style EarlyAdopters fill:#EBF3FA,color:#191919
    style Quantitative fill:#57A3FF,color:#191919
    style Scale fill:#057642,color:#FFF`,
          duration: '2m 30s',
          video_url: '/media/videos/lsn-ls-2.mp4',
          audio_url: '/media/audio/lsn-ls-2.mp3',
          completed: true,
          transcript: [
            { scene: 1, title: 'Introduction', timestamp: '0:00', speaker: 'Lesson 2: The Minimum Viable Product Blueprint.' },
            { scene: 2, title: 'Redefining the MVP', timestamp: '0:04', speaker: 'The MVP is an instrument of validated learning, not sloppy code.' },
            { scene: 3, title: 'Concierge Prototyping', timestamp: '0:08', speaker: 'Deliver the value manually before engineering automated software.' },
            { scene: 4, title: 'Workflow Map', timestamp: '0:12', speaker: 'Observe how early adopter feedback informs scalable automation.' },
            { scene: 5, title: 'Case Study', timestamp: '0:16', speaker: 'Buffer verified pricing tiers before writing a single line of scheduling code.' },
            { scene: 6, title: 'Next Steps', timestamp: '0:20', speaker: 'Cut 50% of your current feature backlog to ship in 7 days.' }
          ]
        }
      ]
    },
    {
      id: 'lvl-ls-2',
      course_id: 'course-lean-startup',
      level_number: 2,
      title: 'Level 2: Steering & Innovation Accounting',
      description: 'Distinguish between actionable metrics and deceptive vanity metrics to make data-backed pivot decisions.',
      lessons: [
        {
          id: 'lsn-ls-3',
          course_id: 'course-lean-startup',
          level_id: 'lvl-ls-2',
          order_index: 3,
          title: 'Actionable Metrics vs. Vanity Metrics',
          short_summary: 'Vanity metrics make you feel good but do not reflect real business health. Actionable metrics demonstrate cause and effect.',
          long_explanation: `Total registered users or page views will almost always trend upwards as long as you spend money on marketing. However, cohort retention, activation rates, and viral coefficient give you the undeniable truth about product-market fit.

Adopt the 3 As of metrics: Actionable, Accessible, and Auditable. When an engineer ships a change, they must be able to directly observe the impact on cohort retention.`,
          key_ideas: [
            'The 3 As of metrics: Actionable, Accessible, and Auditable.',
            'Use cohort analysis to compare how new customer groups behave versus older ones.',
            'Never confuse raw traffic with customer validation.'
          ],
          practical_insights: [
            'Track Week-1, Week-4, and Month-3 retention curves.',
            'Make metrics visible to the entire development squad on a public dashboard.',
            'Tie every new experiment to a specific metric delta.'
          ],
          examples: [
            'IMVU learning that their 3D chat avatar customers preferred using chat with their existing friends.',
            'Grooveshark pivoting based on playlist sharing viral loops rather than sheer banner impressions.'
          ],
          action_items: [
            'Audit your company dashboard and archive 3 vanity metrics.',
            'Implement cohort tracking for your latest user signup flow.',
            'Conduct a split A/B test on your primary activation screen.'
          ],
          mermaid_diagram: `graph TD
    Subscribers["Total Signups (Vanity)"] -.-> FalseConfidence["False Sense of Success"]
    Cohorts["Cohort Retention (Actionable)"] --> Reality["True Product-Market Fit"]
    Reality --> Experimentation["Targeted Improvements"]
    Experimentation --> Growth["Sustainable Scaled Engine"]
    style Subscribers fill:#EF4444,color:#FFF
    style FalseConfidence fill:#F87171,color:#FFF
    style Cohorts fill:#0A66C2,color:#FFF
    style Reality fill:#378FE9,color:#FFF
    style Experimentation fill:#57A3FF,color:#191919
    style Growth fill:#057642,color:#FFF`,
          duration: '2m 30s',
          video_url: '/media/videos/lsn-ls-3.mp4',
          audio_url: '/media/audio/lsn-ls-3.mp3',
          completed: false,
          transcript: [
            { scene: 1, title: 'Introduction', timestamp: '0:00', speaker: 'Lesson 3: Actionable Metrics vs. Vanity Metrics.' },
            { scene: 2, title: 'The Vanity Trap', timestamp: '0:04', speaker: 'Total page views and registered accounts mask true churn.' },
            { scene: 3, title: 'Cohort Retention', timestamp: '0:08', speaker: 'Isolate user groups week by week to see real compounding value.' },
            { scene: 4, title: 'Metrics Framework', timestamp: '0:12', speaker: 'The 3 As: Actionable, Accessible, and Auditable.' },
            { scene: 5, title: 'IMVU Case', timestamp: '0:16', speaker: 'How IMVU discovered real user intent by looking at messaging cohorts.' },
            { scene: 6, title: 'Implementation', timestamp: '0:20', speaker: 'Replace your vanity signups graph with cohort retention curves.' }
          ]
        },
        {
          id: 'lsn-ls-4',
          course_id: 'course-lean-startup',
          level_id: 'lvl-ls-2',
          order_index: 4,
          title: 'The Art of the Pivot: Strategic Course Correction',
          short_summary: 'A pivot is a structured course correction designed to test a new fundamental hypothesis about the product, business model, or engine of growth.',
          long_explanation: `Pivot is not an admission of failure; it is keeping one foot firmly anchored in what you have learned while shifting the other foot into a more lucrative direction. Startups that run out of money fail because they run out of pivots.

Common pivot types include the Zoom-In pivot (focusing on the single feature users love), the Customer Segment pivot, and the Channel pivot.`,
          key_ideas: [
            'Hold regular Pivot or Persevere meetings every 4 to 6 weeks.',
            'Zoom-In Pivot: Refocusing on a single compelling feature that customers adore.',
            'Customer Segment Pivot: Keeping the product but targeting an audience with higher willingness to pay.'
          ],
          practical_insights: [
            'Do not delay pivots out of sunk cost fallacy.',
            'Treat every pivot as a hypothesis that must be validated within 30 days.',
            'Communicate pivot rationale transparently to your investors and team.'
          ],
          examples: [
            'Instagram starting as Burbn, a cluttered location check-in app, and zooming in purely on photos and filters.',
            'Slack starting as an internal chat tool inside a failed gaming venture called Glitch.'
          ],
          action_items: [
            'Schedule a monthly Pivot-or-Persevere review with leadership.',
            'Analyze user feature telemetry to locate your hidden zoom-in runaway feature.',
            'Calculate your startup runway in terms of Pivots Remaining.'
          ],
          mermaid_diagram: `graph LR
    DataCheck["Review Cohort Signals"] --> Evaluation{"Growth Plateaued?"}
    Evaluation -->|Yes| PivotChoice["Select Pivot Strategy: Zoom-In / Segment / Channel"]
    Evaluation -->|No| DoubleDown["Persevere & Optimize Funnel"]
    PivotChoice --> FreshLoop["Initiate New Build-Measure-Learn Loop"]
    style DataCheck fill:#0A66C2,color:#FFF
    style Evaluation fill:#D97706,color:#FFF
    style PivotChoice fill:#378FE9,color:#FFF
    style DoubleDown fill:#057642,color:#FFF
    style FreshLoop fill:#0A66C2,color:#FFF`,
          duration: '2m 30s',
          video_url: '/media/videos/lsn-ls-4.mp4',
          audio_url: '/media/audio/lsn-ls-4.mp3',
          completed: false,
          transcript: [
            { scene: 1, title: 'Introduction', timestamp: '0:00', speaker: 'Lesson 4: The Art of the Strategic Pivot.' },
            { scene: 2, title: 'What is a Pivot?', timestamp: '0:04', speaker: 'Keeping one foot anchored in learning while redirecting strategy.' },
            { scene: 3, title: 'Catalog of Pivots', timestamp: '0:08', speaker: 'Zoom-in, zoom-out, customer segment, and architecture pivots.' },
            { scene: 4, title: 'Decision Framework', timestamp: '0:12', speaker: 'Hold recurring monthly Pivot-or-Persevere leadership evaluations.' },
            { scene: 5, title: 'Famous Pivots', timestamp: '0:16', speaker: 'How Instagram stripped 90% of Burbn to become a mobile photo titan.' },
            { scene: 6, title: 'Next Steps', timestamp: '0:20', speaker: 'Measure startup longevity in pivots remaining, not months of cash.' }
          ]
        }
      ]
    },
    {
      id: 'lvl-ls-3',
      course_id: 'course-lean-startup',
      level_number: 3,
      title: 'Level 3: Acceleration & Engines of Growth',
      description: 'Scale through the 3 Engines of Growth and implement the Five Whys to eliminate systemic defects.',
      lessons: [
        {
          id: 'lsn-ls-5',
          course_id: 'course-lean-startup',
          level_id: 'lvl-ls-3',
          order_index: 5,
          title: 'The Three Engines of Growth',
          short_summary: 'Sustainable growth follows one of three engines: Sticky, Viral, or Paid. Focus relentlessly on one.',
          long_explanation: `Startups often stumble trying to optimize all growth mechanisms simultaneously. The Sticky engine focuses on ultra-low churn; the Viral engine relies on referral loops and coefficients greater than 1.0; the Paid engine scales when Customer Lifetime Value exceeds Cost of Acquisition by at least 3x.`,
          key_ideas: [
            'Sticky Engine: Retaining existing customers compounds recurring revenue.',
            'Viral Engine: Product usage inherently exposes the product to prospective new users.',
            'Paid Engine: Reinvesting marginal gross profit into scalable acquisition channels.'
          ],
          practical_insights: [
            'Pick only ONE primary engine of growth at a time.',
            'For viral growth, reduce friction in the invite or share flow to zero.',
            'For paid growth, measure payback period in months.'
          ],
          examples: [
            'Hotmail attaching P.S. Get your free email at Hotmail to every outgoing email.',
            'eBay benefiting from sticky network effects where buyers attracted sellers.'
          ],
          action_items: [
            'Classify your current product into its primary growth engine.',
            'Measure your viral coefficient (k-factor) or churn rate.',
            'Eliminate paid marketing spend if your LTV is less than 3x CAC.'
          ],
          mermaid_diagram: `graph TD
    Engines["Engines of Growth"] --> Sticky["1. Sticky Engine (Low Churn)"]
    Engines --> Viral["2. Viral Engine (k > 1.0)"]
    Engines --> Paid["3. Paid Engine (LTV > 3x CAC)"]
    Sticky --> Compounding["High Retention Compounding"]
    Viral --> Organic["Exponential Network Growth"]
    Paid --> Reinvestment["Profitable Reinvestment Cycle"]
    style Engines fill:#0A66C2,color:#FFF
    style Sticky fill:#378FE9,color:#FFF
    style Viral fill:#57A3FF,color:#191919
    style Paid fill:#057642,color:#FFF`,
          duration: '2m 30s',
          video_url: '/media/videos/lsn-ls-5.mp4',
          audio_url: '/media/audio/lsn-ls-5.mp3',
          completed: false,
          transcript: [
            { scene: 1, title: 'Introduction', timestamp: '0:00', speaker: 'Lesson 5: The Three Engines of Growth.' },
            { scene: 2, title: 'Engine Typology', timestamp: '0:04', speaker: 'Identify whether your product is Sticky, Viral, or Paid.' },
            { scene: 3, title: 'The Sticky Engine', timestamp: '0:08', speaker: 'Defeating churn is the fastest route to compounding recurring MRR.' },
            { scene: 4, title: 'The Viral & Paid Loops', timestamp: '0:12', speaker: 'Viral k-factor greater than 1.0 and unit economics with 3x LTV/CAC.' },
            { scene: 5, title: 'Hotmail & eBay', timestamp: '0:16', speaker: 'Classic executions that dominated by perfecting a single engine.' },
            { scene: 6, title: 'Execution', timestamp: '0:20', speaker: 'Focus your product squad on one primary growth metric.' }
          ]
        },
        {
          id: 'lsn-ls-6',
          course_id: 'course-lean-startup',
          level_id: 'lvl-ls-3',
          order_index: 6,
          title: 'The Five Whys: Root Cause Problem Solving',
          short_summary: 'When technical or human failures arise, ask Why? five times to identify the root cause and build proportional preventive investments.',
          long_explanation: `Behind every seemingly technical problem is a human problem. The Five Whys method ties rate of progress to institutional learning. When a server goes down or a critical bug ships, rather than pointing fingers, the team diagnoses systemic failure and invests proportionally to fix the underlying process.`,
          key_ideas: [
            'Ask Why? five consecutive times to trace back to human training and process gaps.',
            'Make proportional investments at every level of the Five Whys chain.',
            'Foster a blameless culture focused on fixing systems, not punishing individuals.'
          ],
          practical_insights: [
            'Hold Five Whys meetings with all affected team members within 24 hours of an outage.',
            'Assign clear owners and deadlines to the preventive action items.',
            'Start with small proportional investments to avoid bureaucratic gridlock.'
          ],
          examples: [
            'A failed server deployment leading to discovering the absence of automated staging test scripts.',
            'Toyota resolving machine breakdowns by discovering clogged lubrication strainers.'
          ],
          action_items: [
            'Conduct a 5 Whys retrospective on the latest customer escalation.',
            'Implement an automated test or checklist for the root cause found.',
            'Commit to blameless operational retrospectives.'
          ],
          mermaid_diagram: `graph TD
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
    style Prevention fill:#10B981,color:#FFF`,
          duration: '2m 30s',
          video_url: '/media/videos/lsn-ls-6.mp4',
          audio_url: '/media/audio/lsn-ls-6.mp3',
          completed: false,
          transcript: [
            { scene: 1, title: 'Introduction', timestamp: '0:00', speaker: 'Lesson 6: The Five Whys Root Cause Method.' },
            { scene: 2, title: 'Human vs Technical Bugs', timestamp: '0:04', speaker: 'Every technical malfunction points to a systemic training gap.' },
            { scene: 3, title: 'The Five Whys Ladder', timestamp: '0:08', speaker: 'Trace failure back to root operational and procedural causes.' },
            { scene: 4, title: 'Proportional Investments', timestamp: '0:12', speaker: 'Invest in prevention at all five stages of the breakdown chain.' },
            { scene: 5, title: 'Toyota Legacy', timestamp: '0:16', speaker: 'How lean manufacturing turned errors into continuous learning.' },
            { scene: 6, title: 'Final Certification', timestamp: '0:20', speaker: 'Congratulations! You are now prepared for the Chapter Assessment.' }
          ]
        }
      ]
    }
  ],
  flashcards: [
    {
      id: 'fc-1',
      course_id: 'course-lean-startup',
      question: 'What is the primary definition of a startup according to Eric Ries?',
      answer: 'A human institution designed to deliver a new product or service under conditions of extreme uncertainty.',
      category: 'Foundations',
      mastered: true
    },
    {
      id: 'fc-2',
      course_id: 'course-lean-startup',
      question: 'What is the core purpose of a Minimum Viable Product (MVP)?',
      answer: 'To collect the maximum amount of validated learning about customers with the least development effort.',
      category: 'Product Development',
      mastered: true
    },
    {
      id: 'fc-3',
      course_id: 'course-lean-startup',
      question: 'What are the three steps in the core Lean Startup feedback loop?',
      answer: 'Build -> Measure -> Learn (repeated continuously at maximum cycle speed).',
      category: 'Methodology',
      mastered: false
    },
    {
      id: 'fc-4',
      course_id: 'course-lean-startup',
      question: 'What is a Vanity Metric?',
      answer: 'A metric (like raw page views or total signups) that increases regardless of whether the business is healthy or retaining users.',
      category: 'Metrics',
      mastered: false
    },
    {
      id: 'fc-5',
      course_id: 'course-lean-startup',
      question: 'What are the three As of actionable metrics?',
      answer: 'Actionable, Accessible, and Auditable.',
      category: 'Metrics',
      mastered: false
    },
    {
      id: 'fc-6',
      course_id: 'course-lean-startup',
      question: 'What constitutes a Zoom-In Pivot?',
      answer: 'Refocusing an entire product around a single high-performing feature that customers love.',
      category: 'Strategy',
      mastered: false
    },
    {
      id: 'fc-7',
      course_id: 'course-lean-startup',
      question: 'What are the Three Engines of Growth?',
      answer: 'The Sticky Engine, the Viral Engine, and the Paid Engine.',
      category: 'Growth',
      mastered: false
    },
    {
      id: 'fc-8',
      course_id: 'course-lean-startup',
      question: 'What must the viral coefficient (k) be for exponential organic viral growth?',
      answer: 'Greater than 1.0 (meaning each user successfully recruits more than one additional user).',
      category: 'Growth',
      mastered: false
    },
    {
      id: 'fc-9',
      course_id: 'course-lean-startup',
      question: 'What is the purpose of the Five Whys methodology?',
      answer: 'To identify the root human and process causes behind technical failures and make proportional preventive investments.',
      category: 'Operations',
      mastered: false
    },
    {
      id: 'fc-10',
      course_id: 'course-lean-startup',
      question: 'Why is validated learning superior to shipping features on time?',
      answer: 'Because building a product on time that nobody wants is 100% waste.',
      category: 'Mindset',
      mastered: false
    },
    {
      id: 'fc-11',
      course_id: 'course-lean-startup',
      question: 'What is a Concierge MVP?',
      answer: 'An MVP where the service is provided completely manually to early adopters to observe their real needs before coding.',
      category: 'Prototyping',
      mastered: false
    },
    {
      id: 'fc-12',
      course_id: 'course-lean-startup',
      question: 'What is Innovation Accounting?',
      answer: 'A quantitative framework to establish a baseline, tune the engine, and decide whether to pivot or persevere objectively.',
      category: 'Finance & Strategy',
      mastered: false
    }
  ]
};

export const DEMO_QUIZZES: QuizQuestion[] = [
  {
    id: 'quiz-1',
    course_id: 'course-lean-startup',
    question: 'Which of the following is the true objective of a Minimum Viable Product (MVP)?',
    options: [
      'To ship a buggy prototype to prove you can code fast',
      'To begin the process of validated learning as quickly as possible',
      'To earn maximum revenue on day one',
      'To replace all future design and engineering work'
    ],
    correct_index: 1,
    explanation: 'The MVP is specifically engineered to test core value hypotheses with minimal effort and accelerate learning.'
  },
  {
    id: 'quiz-2',
    course_id: 'course-lean-startup',
    question: 'Why are cohort metrics vastly superior to cumulative totals?',
    options: [
      'They look more impressive on investor decks',
      'They isolate the behavior of specific customer segments over time to reveal genuine retention',
      'They require fewer data scientists to calculate',
      'They always show positive growth numbers'
    ],
    correct_index: 1,
    explanation: 'Cohorts expose whether newer product iterations are truly retaining users or if churn is disguised by raw acquisition.'
  },
  {
    id: 'quiz-3',
    course_id: 'course-lean-startup',
    question: 'In the Build-Measure-Learn feedback loop, what is the most important optimization goal?',
    options: [
      'Writing the maximum number of lines of code per day',
      'Minimizing the total cycle time through the entire loop',
      'Spending the largest possible budget on paid advertising',
      'Holding daily 4-hour status meetings'
    ],
    correct_index: 1,
    explanation: 'The startup that executes validated Build-Measure-Learn cycles the fastest discovers product-market fit before runway expires.'
  },
  {
    id: 'quiz-4',
    course_id: 'course-lean-startup',
    question: 'What characterizes a Zoom-In Pivot?',
    options: [
      'Buying larger computer monitors for the engineering squad',
      'Refocusing the entire product offering on a single feature that users already love',
      'Increasing the retail price of the software by 500%',
      'Switching from B2B enterprise sales to consumer gaming'
    ],
    correct_index: 1,
    explanation: 'Instagram famously executed a Zoom-In pivot by taking the photo filter feature from Burbn and discarding the rest.'
  },
  {
    id: 'quiz-5',
    course_id: 'course-lean-startup',
    question: 'What is the primary diagnostic principle of the Five Whys technique?',
    options: [
      'Assigning blame to the junior engineer who pushed the commit',
      'Treating every technical failure as a manifestation of an underlying human/process flaw',
      'Asking the customer why they bought from a competitor five times',
      'Deleting the codebase and starting from scratch'
    ],
    correct_index: 1,
    explanation: 'Technical breakdowns are symptoms; asking Five Whys exposes root process, training, or architectural oversights.'
  },
  {
    id: 'quiz-6',
    course_id: 'course-lean-startup',
    question: 'Which of the following is required for the Paid Engine of Growth to be sustainable?',
    options: [
      'Customer Acquisition Cost (CAC) must exceed Lifetime Value (LTV)',
      'Customer Lifetime Value (LTV) must comfortably exceed Acquisition Cost (CAC) with positive unit economics',
      'You must run super bowl commercials annually',
      'You must offer the product entirely free forever'
    ],
    correct_index: 1,
    explanation: 'The Paid Engine compounds only when marginal profit from each customer funds the acquisition of more than one new customer.'
  }
];
