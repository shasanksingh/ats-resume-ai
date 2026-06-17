TECH_SKILLS = [
    # Programming and software engineering
    "python", "java", "javascript", "typescript", "sql", "r", "c", "c++",
    "c#", ".net", "php", "ruby", "go", "rust", "bash", "powershell",
    "data structures", "algorithms", "oop", "design patterns", "system design",
    "software development lifecycle", "agile", "scrum", "debugging", "testing",
    "unit testing", "integration testing", "code review", "git", "github",

    # Frontend, mobile, and full stack
    "html", "css", "react", "nextjs", "angular", "vue", "tailwind",
    "bootstrap", "redux", "web accessibility", "responsive design",
    "nodejs", "express", "spring boot", "flutter", "react native", "android",
    "ios", "rest api", "graphql", "websocket",

    # Backend, databases, and distributed systems
    "fastapi", "flask", "django", "microservices", "authentication",
    "authorization", "oauth", "caching", "queues", "event driven architecture",
    "mysql", "postgresql", "sql server", "oracle", "mongodb", "redis",
    "dynamodb", "stored procedures", "views", "triggers", "indexes",
    "query optimization", "performance tuning", "normalization", "joins",
    "window functions", "cte", "database design",

    # Cloud, DevOps, SRE, and platform
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "ci/cd", "linux",
    "observability", "monitoring", "prometheus", "grafana", "elk stack",
    "incident response", "site reliability engineering", "load balancing",
    "nginx", "serverless", "infrastructure as code",

    # Data engineering, analytics, and BI
    "excel", "power bi", "tableau", "looker", "data visualization",
    "dashboarding", "data cleaning", "data analysis",
    "exploratory data analysis", "eda", "kpi", "metrics", "a/b testing",
    "statistical analysis", "forecasting", "etl", "elt", "data modeling",
    "data warehouse", "data lake", "snowflake", "bigquery", "redshift",
    "spark", "hadoop", "kafka", "airflow", "dbt", "ssis", "ssrs",
    "pandas", "numpy",

    # AI, machine learning, and GenAI
    "machine learning", "deep learning", "nlp", "computer vision",
    "generative ai", "rag", "llm", "langchain", "hugging face",
    "transformers", "embeddings", "semantic search", "faiss",
    "vector database", "model evaluation", "feature engineering",
    "mlops", "scikit-learn", "tensorflow", "pytorch",

    # Quality assurance and test engineering
    "quality assurance", "manual testing", "automation testing",
    "functional testing", "regression testing", "smoke testing",
    "end-to-end testing", "api testing", "ui automation", "test planning",
    "test case design", "test execution", "defect tracking", "bug reporting",
    "stlc", "sdlc", "selenium", "cypress", "playwright", "postman",
    "pytest", "junit", "testng", "jira", "performance testing", "jmeter",
    "load testing", "mobile testing", "uat",

    # Cybersecurity, networking, and IT support
    "cybersecurity", "network security", "information security",
    "vulnerability assessment", "penetration testing", "siem",
    "soc", "iam", "firewall", "ids", "ips", "wireshark", "nmap",
    "splunk", "risk assessment", "security compliance", "iso 27001",
    "tcp/ip", "dns", "dhcp", "vpn", "routing", "switching", "lan", "wan",
    "cisco", "active directory", "microsoft 365", "windows server",
    "technical support", "help desk", "desktop support", "troubleshooting",
    "ticketing system", "service desk", "itil", "hardware support",
    "software installation", "remote support", "customer support",

    # Electrical and electronics engineering
    "electrical engineering", "circuit design", "power systems",
    "power distribution", "electrical maintenance", "control systems",
    "plc", "scada", "matlab", "simulink", "embedded systems",
    "microcontrollers", "pcb design", "vlsi", "signal processing",
    "electrical safety", "relay protection", "transformers",
    "switchgear", "autocad electrical", "solar energy", "renewable energy",

    # Mechanical and manufacturing engineering
    "mechanical engineering", "solidworks", "catia", "creo", "autocad",
    "ansys", "cad", "cam", "fea", "cfd", "gd&t", "thermodynamics",
    "fluid mechanics", "heat transfer", "machine design", "hvac",
    "manufacturing", "cnc", "lean manufacturing", "six sigma",
    "preventive maintenance", "root cause analysis", "quality control",
    "production planning", "bom",

    # Civil, construction, and architecture
    "civil engineering", "structural engineering", "construction management",
    "site engineering", "quantity surveying", "estimation", "costing",
    "billing", "surveying", "staad pro", "etabs", "revit", "bim",
    "primavera p6", "ms project", "project scheduling", "concrete",
    "steel structures", "geotechnical engineering", "transportation engineering",
    "water resources", "quality inspection", "site safety",

    # Product, project, operations, and supply chain
    "product management", "product strategy", "roadmap", "user stories",
    "requirements gathering", "business analysis", "stakeholder management",
    "project management", "risk management", "budget management",
    "vendor management", "operations management", "process improvement",
    "supply chain", "logistics", "inventory management", "procurement",
    "demand planning", "warehouse management", "sap", "erp",

    # Finance, accounting, HR, sales, and customer-facing roles
    "accounting", "financial analysis", "financial reporting", "budgeting",
    "bookkeeping", "accounts payable", "accounts receivable", "taxation",
    "auditing", "tally", "quickbooks", "reconciliation", "gst",
    "human resources", "recruitment", "talent acquisition", "onboarding",
    "payroll", "employee engagement", "performance management",
    "labor law", "hris", "sales", "business development", "lead generation",
    "crm", "salesforce", "negotiation", "account management",
    "customer success", "customer relationship management",

    # Marketing, design, and content
    "seo", "sem", "google analytics", "ga4", "google ads", "meta ads",
    "email marketing", "marketing automation", "hubspot", "mailchimp",
    "content strategy", "campaign management", "conversion rate optimization",
    "cro", "social media marketing", "keyword research", "landing pages",
    "ui design", "ux design", "user research", "wireframing", "prototyping",
    "figma", "adobe xd", "photoshop", "illustrator", "content writing",

    # Healthcare and life sciences
    "patient care", "clinical documentation", "medical terminology",
    "electronic health records", "ehr", "hipaa", "clinical research",
    "pharmacovigilance", "good clinical practice", "gcp compliance",
    "laboratory testing", "quality management system", "qms",

    # Common tools and business capabilities
    "swagger", "api integration", "automation", "scripting", "web scraping",
    "ms office", "communication", "team leadership", "problem solving",
    "documentation", "reporting", "presentation", "time management",
]


SKILL_ALIASES = {
    "rest api": ["api", "apis", "restful api", "restful apis", "api development"],
    "google analytics": ["analytics", "web analytics"],
    "ga4": ["google analytics 4"],
    "power bi": ["powerbi"],
    "a/b testing": ["ab testing", "split testing"],
    "postgresql": ["postgres"],
    "nodejs": ["node.js", "node js"],
    "nextjs": ["next.js"],
    "machine learning": ["ml"],
    "generative ai": ["genai", "gen ai"],
    "data visualization": ["visualization", "charts", "dashboards"],
    "query optimization": ["query tuning", "sql optimization"],
    "quality assurance": ["qa", "software quality assurance"],
    "end-to-end testing": ["e2e testing", "end to end testing"],
    "ci/cd": ["ci cd", "cicd", "continuous integration", "continuous delivery"],
    "technical support": ["it support", "tech support"],
    "help desk": ["helpdesk", "service desk"],
    "active directory": ["ad", "azure ad", "entra id"],
    "microsoft 365": ["office 365", "o365"],
    "electrical engineering": ["electrical engineer"],
    "mechanical engineering": ["mechanical engineer"],
    "civil engineering": ["civil engineer"],
    "project management": ["project manager"],
    "product management": ["product manager"],
    "human resources": ["hr"],
    "customer relationship management": ["crm"],
    "electronic health records": ["electronic medical records", "emr"],
    "infrastructure as code": ["iac"],
    "site reliability engineering": ["sre"],
    "root cause analysis": ["rca"],
    "quality management system": ["qms"],
}
