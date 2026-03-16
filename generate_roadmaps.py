"""
generate_roadmaps.py
Wipes and re-seeds all roadmaps + topic nodes + curated free resource links.
Run inside Docker:  docker compose exec web python generate_roadmaps.py
"""
from app import create_app
from app.extensions import db
from app.models.roadmap import Roadmap, RoadmapNode
from app.models.node_resource import NodeResource
from sqlalchemy import text

# ─────────────────────────────────────────────────────────────────────────────
#  ROADMAP DATA
#  Each node: (title, order_index, [ (resource_title, url, type), ... ])
# ─────────────────────────────────────────────────────────────────────────────
ROADMAPS = [
  {
    "title": "Frontend Developer",
    "description": "From HTML fundamentals to production-grade React/Next.js applications.",
    "nodes": [
      ("Internet Basics & How Browsers Work", 1, [
        ("How the Internet Works – CS50 (Free)", "https://www.youtube.com/watch?v=n_KghQP86Sw", "Video"),
        ("How Browsers Work – web.dev", "https://web.dev/articles/howbrowserswork", "Article"),
      ]),
      ("HTML5 — Semantic Markup & Accessibility", 2, [
        ("HTML Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=pQN-pnXPaVg", "Video"),
        ("The Odin Project – HTML Foundations", "https://www.theodinproject.com/paths/foundations/courses/foundations", "Course"),
      ]),
      ("CSS3 — Flexbox, Grid & Animations", 3, [
        ("Kevin Powell – CSS for Beginners (YouTube)", "https://www.youtube.com/@KevinPowell", "Video"),
        ("CSS Flexbox – freeCodeCamp", "https://www.youtube.com/watch?v=-Wlt8NRtOpo", "Video"),
        ("CSS Grid – Fireship (11 min)", "https://www.youtube.com/watch?v=uuOXPWCh-6o", "Video"),
      ]),
      ("JavaScript (ES6+) — Core Language", 4, [
        ("JavaScript.info – Full Modern Tutorial", "https://javascript.info/", "Course"),
        ("JS Crash Course – Traversy Media", "https://www.youtube.com/watch?v=hdI2bqOjy3c", "Video"),
        ("Eloquent JavaScript (Free Book)", "https://eloquentjavascript.net/", "Article"),
      ]),
      ("TypeScript — Static Typing", 5, [
        ("TypeScript Handbook – Official Docs", "https://www.typescriptlang.org/docs/", "Docs"),
        ("No BS TypeScript – Jack Herrington (YouTube)", "https://www.youtube.com/playlist?list=PLNqp92_EXZBJYFrpEzdO2EapvU0GOJ09n", "Video"),
        ("Total TypeScript – Matt Pocock (Free Tier)", "https://www.totaltypescript.com/tutorials", "Course"),
      ]),
      ("Version Control with Git & GitHub", 6, [
        ("Git & GitHub Crash Course – freeCodeCamp", "https://www.youtube.com/watch?v=RGOj5yH7evk", "Video"),
        ("Pro Git Book (Free)", "https://git-scm.com/book/en/v2", "Article"),
      ]),
      ("React — Components, Hooks, Context", 7, [
        ("React Official Docs (react.dev)", "https://react.dev/learn", "Docs"),
        ("React Full Course 2024 – Dave Gray", "https://www.youtube.com/watch?v=RVFAyFWO4go", "Video"),
        ("Scrimba React Course (Free)", "https://scrimba.com/learn/learnreact", "Course"),
      ]),
      ("Next.js — SSR, SSG, App Router", 8, [
        ("Next.js Official Docs", "https://nextjs.org/docs", "Docs"),
        ("Next.js 14 Full Course – Dave Gray", "https://www.youtube.com/watch?v=wm5gMKuwSYk", "Video"),
      ]),
      ("State Management — Zustand / Redux Toolkit", 9, [
        ("Redux Toolkit Tutorial – Dave Gray", "https://www.youtube.com/watch?v=NqzdVN2tyvQ", "Video"),
        ("Zustand Docs & Guide", "https://zustand-demo.pmnd.rs/", "Docs"),
      ]),
      ("Testing — Jest, React Testing Library", 10, [
        ("React Testing Library – Web Dev Simplified", "https://www.youtube.com/watch?v=7dTTFW7yACQ", "Video"),
        ("Testing JavaScript – Kent C. Dodds (Free Tier)", "https://testingjavascript.com/", "Course"),
      ]),
      ("Web Performance & Core Web Vitals", 11, [
        ("web.dev Performance Guide", "https://web.dev/performance", "Article"),
        ("Performance Optimization – Fireship", "https://www.youtube.com/watch?v=0fONene3OIA", "Video"),
      ]),
      ("CI/CD — GitHub Actions, Vercel", 12, [
        ("GitHub Actions in 20 min – Fireship", "https://www.youtube.com/watch?v=eB0nUzAI7M8", "Video"),
        ("GitHub Actions Docs", "https://docs.github.com/en/actions", "Docs"),
      ]),
    ]
  },
  {
    "title": "Backend Developer",
    "description": "APIs, databases, system design — the engine behind every great product.",
    "nodes": [
      ("Internet Networking & OSI Model", 1, [
        ("Computer Networking Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=qiQR5rTSshw", "Video"),
        ("Fireship – OSI Model in 7 min", "https://www.youtube.com/watch?v=vv4y_uOneC0", "Video"),
      ]),
      ("Linux & Shell Scripting Fundamentals", 2, [
        ("Linux Command Line – freeCodeCamp", "https://www.youtube.com/watch?v=ZtqBQ68cfJc", "Video"),
        ("The Missing Semester of CS (MIT, Free)", "https://missing.csail.mit.edu/", "Course"),
      ]),
      ("Python — Core & Advanced Patterns", 3, [
        ("Python Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=rfscVS0vtbw", "Video"),
        ("Corey Schafer Python Tutorials", "https://www.youtube.com/playlist?list=PL-osiE80TeTt2d9bfVyTiXJA-UTHn6WwU", "Video"),
        ("Python Institute – PCEP Free Course", "https://pythoninstitute.org/pcep", "Course"),
      ]),
      ("SQL — PostgreSQL Deep Dive", 4, [
        ("PostgreSQL Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=qw--VYLpxG4", "Video"),
        ("Use the Index, Luke (Free Book)", "https://use-the-index-luke.com/", "Article"),
        ("CMU Intro to Databases 2023 (YouTube)", "https://www.youtube.com/playlist?list=PLSE8ODhjZXjbj8BMuIrRcacnQh20hmY9g", "Video"),
      ]),
      ("NoSQL — MongoDB & Redis", 5, [
        ("MongoDB Crash Course – Web Dev Simplified", "https://www.youtube.com/watch?v=ofme2o29ngU", "Video"),
        ("Redis in 100 Seconds – Fireship", "https://www.youtube.com/watch?v=G1rOthIU-uo", "Video"),
      ]),
      ("REST API Design & OpenAPI Spec", 6, [
        ("REST API Best Practices – freeCodeCamp", "https://www.freecodecamp.org/news/rest-api-best-practices-rest-endpoint-design-examples/", "Article"),
        ("HTTP Crash Course – Traversy Media", "https://www.youtube.com/watch?v=iYM2zFP3Zn0", "Video"),
      ]),
      ("Flask / FastAPI — Building Microservices", 7, [
        ("FastAPI Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=0sOvCWFmrtA", "Video"),
        ("Flask Official Tutorial (Docs)", "https://flask.palletsprojects.com/en/latest/tutorial/", "Docs"),
        ("TestDriven.io – FastAPI TDD (Free Chapters)", "https://testdriven.io/blog/fastapi-crud/", "Article"),
      ]),
      ("Authentication — JWT, OAuth2, Sessions", 8, [
        ("OAuth2 Explained – Web Dev Simplified", "https://www.youtube.com/watch?v=996OiexHze0", "Video"),
        ("JWT.io Introduction", "https://jwt.io/introduction", "Article"),
      ]),
      ("System Design — Scaling & Distributed Systems", 9, [
        ("System Design Primer (GitHub, Free)", "https://github.com/donnemartin/system-design-primer", "Article"),
        ("Gaurav Sen – System Design Playlist", "https://www.youtube.com/playlist?list=PLMCXHnjXnTnvo6alSjVkgxV-VH6EPyvoX", "Video"),
        ("ByteByteGo System Design (YouTube)", "https://www.youtube.com/@ByteByteGo", "Video"),
      ]),
      ("Caching Strategies — Redis & CDN", 10, [
        ("Caching Explained – Fireship", "https://www.youtube.com/watch?v=U3RkDLtS7uY", "Video"),
        ("Redis Caching – Traversy Media", "https://www.youtube.com/watch?v=jgpVdJB2sKQ", "Video"),
      ]),
      ("Message Queues — RabbitMQ / Kafka", 11, [
        ("Apache Kafka in 100 Seconds – Fireship", "https://www.youtube.com/watch?v=uvb00oaa3k8", "Video"),
        ("Kafka Tutorial – freeCodeCamp", "https://www.youtube.com/watch?v=SqVfCyfCJqw", "Video"),
      ]),
      ("Security — OWASP Top 10", 12, [
        ("OWASP Top 10 Explained – Fireship", "https://www.youtube.com/watch?v=Fbe7EZAGnOU", "Video"),
        ("OWASP Official Cheat Sheet", "https://cheatsheetseries.owasp.org/", "Docs"),
      ]),
    ]
  },
  {
    "title": "DevOps & Cloud Engineer",
    "description": "From containers to Kubernetes — mastering modern infrastructure.",
    "nodes": [
      ("Linux Administration", 1, [
        ("Linux Admin Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=wBp0Rb-ZJak", "Video"),
        ("Linux Journey (Interactive, Free)", "https://linuxjourney.com/", "Course"),
      ]),
      ("Docker & Containerisation", 2, [
        ("Docker Tutorial – TechWorld with Nana", "https://www.youtube.com/watch?v=3c-iBn73dDE", "Video"),
        ("Play with Docker (Free Browser Lab)", "https://labs.play-with-docker.com/", "Course"),
      ]),
      ("Docker Compose — Local Orchestration", 3, [
        ("Docker Compose in 12 min – Fireship", "https://www.youtube.com/watch?v=Qw9zlE3t8Ko", "Video"),
        ("Official Docker Compose Docs", "https://docs.docker.com/compose/", "Docs"),
      ]),
      ("Kubernetes — Pods, Deployments, Services", 4, [
        ("Kubernetes Full Course – TechWorld with Nana", "https://www.youtube.com/watch?v=X48VuDVv0do", "Video"),
        ("KillerCoda – Interactive K8s Labs (Free)", "https://killercoda.com/", "Course"),
      ]),
      ("Infrastructure as Code — Terraform", 5, [
        ("Terraform Crash Course – freeCodeCamp", "https://www.youtube.com/watch?v=SLB_c_ayRMo", "Video"),
        ("HashiCorp Learn Terraform (Free)", "https://developer.hashicorp.com/terraform/tutorials", "Course"),
      ]),
      ("AWS / GCP / Azure Core Services", 6, [
        ("AWS Free Tier + Training (Official)", "https://aws.amazon.com/training/", "Course"),
        ("Cloud Computing Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=M988_fsOSWo", "Video"),
      ]),
      ("CI/CD Pipelines — GitHub Actions, GitLab CI", 7, [
        ("GitHub Actions Full Course – TechWorld with Nana", "https://www.youtube.com/watch?v=R8_veQiYBjI", "Video"),
        ("GitLab CI Tutorial – TechWorld with Nana", "https://www.youtube.com/watch?v=qP8kir2GUgo", "Video"),
      ]),
      ("Monitoring & Observability — Prometheus, Grafana", 8, [
        ("Prometheus & Grafana – TechWorld with Nana", "https://www.youtube.com/watch?v=h4Sl21AKiDg", "Video"),
        ("Play with Grafana Labs (Free)", "https://play.grafana.org/", "Course"),
      ]),
      ("GitOps — ArgoCD / Flux", 9, [
        ("ArgoCD Tutorial – TechWorld with Nana", "https://www.youtube.com/watch?v=MeU5_k9ssrs", "Video"),
        ("OpenGitOps Documentation", "https://opengitops.dev/", "Docs"),
      ]),
    ]
  },
  {
    "title": "AI & Machine Learning Engineer",
    "description": "From maths foundations to deploying large language models in production.",
    "nodes": [
      ("Linear Algebra & Calculus for ML", 1, [
        ("3Blue1Brown – Essence of Linear Algebra", "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab", "Video"),
        ("Khan Academy – Linear Algebra (Free)", "https://www.khanacademy.org/math/linear-algebra", "Course"),
      ]),
      ("Statistics & Probability", 2, [
        ("Statistics – StatQuest (YouTube)", "https://www.youtube.com/@statquest", "Video"),
        ("Khan Academy – Statistics & Probability (Free)", "https://www.khanacademy.org/math/statistics-probability", "Course"),
      ]),
      ("Python for Data Science — NumPy, Pandas", 3, [
        ("NumPy & Pandas – Corey Schafer", "https://www.youtube.com/watch?v=ZyhVh-qRZPA", "Video"),
        ("Kaggle Python Course (Free)", "https://www.kaggle.com/learn/python", "Course"),
      ]),
      ("Classical ML — Scikit-Learn", 4, [
        ("ML with Scikit-Learn – Sentdex", "https://www.youtube.com/playlist?list=PLQVvvaa0QuDd0flgGphKCej-9jp-QdzZ3", "Video"),
        ("Kaggle Intro to ML (Free)", "https://www.kaggle.com/learn/intro-to-machine-learning", "Course"),
      ]),
      ("Deep Learning Fundamentals — Neural Networks", 5, [
        ("Neural Networks – 3Blue1Brown", "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi", "Video"),
        ("fast.ai – Practical Deep Learning (Free)", "https://course.fast.ai/", "Course"),
      ]),
      ("PyTorch & Training Loops", 6, [
        ("PyTorch in 25 min – Andrej Karpathy", "https://www.youtube.com/watch?v=VMj-3S1tku0", "Video"),
        ("Official PyTorch Tutorials (Free)", "https://pytorch.org/tutorials/", "Docs"),
      ]),
      ("NLP — Transformers, BERT, Tokenisation", 7, [
        ("Hugging Face NLP Course (Free)", "https://huggingface.co/learn/nlp-course/chapter1/1", "Course"),
        ("Andrej Karpathy – Let's build GPT from scratch", "https://www.youtube.com/watch?v=kCc8FmEb1nY", "Video"),
      ]),
      ("Large Language Models & Fine-Tuning", 8, [
        ("LLM Fine-Tuning – Hugging Face (Free)", "https://huggingface.co/docs/trl/index", "Docs"),
        ("Andrej Karpathy – Intro to LLMs (1hr)", "https://www.youtube.com/watch?v=zjkBMFhNj_g", "Video"),
      ]),
      ("Retrieval-Augmented Generation (RAG)", 9, [
        ("RAG from Scratch – LangChain (YouTube)", "https://www.youtube.com/playlist?list=PLfaIDFEXuae2LXbO1_PKyVJiQ23ZztA0x", "Video"),
        ("LlamaIndex Docs – Build RAG Apps (Free)", "https://docs.llamaindex.ai/en/stable/", "Docs"),
      ]),
      ("MLOps — MLflow, DVC, Model Serving", 10, [
        ("MLOps Course – freeCodeCamp", "https://www.youtube.com/watch?v=Mf8SnUg874w", "Video"),
        ("Made with ML – MLOps Guide (Free)", "https://madewithml.com/", "Course"),
      ]),
    ]
  },
  {
    "title": "Full-Stack Developer",
    "description": "End-to-end ownership: React on the frontend, Node/Python on the backend.",
    "nodes": [
      ("HTML5, CSS3, JavaScript (ES6+)", 1, [
        ("The Odin Project – Foundations (Free)", "https://www.theodinproject.com/paths/foundations", "Course"),
        ("freeCodeCamp – Responsive Web Design", "https://www.freecodecamp.org/learn/2022/responsive-web-design/", "Course"),
      ]),
      ("React — Hooks & Component Patterns", 2, [
        ("React in 1 Hour – Mosh", "https://www.youtube.com/watch?v=SqcY0GlETPk", "Video"),
        ("React Official Docs – react.dev", "https://react.dev/learn", "Docs"),
      ]),
      ("Next.js Full-Stack with App Router", 3, [
        ("Next.js 14 Official Tutorial", "https://nextjs.org/learn", "Course"),
        ("Next.js Crash Course – Traversy Media", "https://www.youtube.com/watch?v=mTz0GXj8NN0", "Video"),
      ]),
      ("Node.js & Express Fundamentals", 4, [
        ("Node.js Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=Oe421EPjeBE", "Video"),
        ("The Odin Project – NodeJS Path (Free)", "https://www.theodinproject.com/paths/full-stack-javascript", "Course"),
      ]),
      ("PostgreSQL & Prisma ORM", 5, [
        ("Prisma Crash Course – Web Dev Simplified", "https://www.youtube.com/watch?v=RebA5J-rlwg", "Video"),
        ("Prisma Docs – Quickstart (Free)", "https://www.prisma.io/docs/getting-started/quickstart", "Docs"),
      ]),
      ("Authentication — NextAuth / JWT", 6, [
        ("NextAuth.js Tutorial – Traversy Media", "https://www.youtube.com/watch?v=md65iBX5Gxg", "Video"),
        ("NextAuth.js Official Docs", "https://next-auth.js.org/getting-started/introduction", "Docs"),
      ]),
      ("Docker for Development", 7, [
        ("Docker for Beginners – Fireship", "https://www.youtube.com/watch?v=gAkwW2tuIqE", "Video"),
        ("Docker Get Started Guide (Free)", "https://docs.docker.com/get-started/", "Docs"),
      ]),
      ("Cloud Deployment — Vercel, Railway, Fly.io", 8, [
        ("Deploy to Vercel in 5 min – Fireship", "https://www.youtube.com/watch?v=ouzY-64--Lk", "Video"),
        ("Fly.io Documentation (Free Tier)", "https://fly.io/docs/", "Docs"),
      ]),
    ]
  },
  {
    "title": "Cybersecurity Engineer",
    "description": "Defensive and offensive security — CTFs, pentesting, and secure design.",
    "nodes": [
      ("Networking Fundamentals & Wireshark", 1, [
        ("Wireshark Full Course – David Bombal", "https://www.youtube.com/watch?v=aEADJjcEqlg", "Video"),
        ("Professor Messer – CompTIA Network+ (Free)", "https://www.professormesser.com/network-plus/n10-008/n10-008-video/n10-008-training-course/", "Course"),
      ]),
      ("OWASP Top 10 Web Security Risks", 2, [
        ("OWASP Top 10 Explained by Fireship", "https://www.youtube.com/watch?v=Fbe7EZAGnOU", "Video"),
        ("OWASP WebGoat – Learn by Hacking (Free)", "https://owasp.org/www-project-webgoat/", "Course"),
      ]),
      ("Cryptography — Hashing, TLS, PKI", 3, [
        ("cryptography Crash Course – CS50", "https://www.youtube.com/watch?v=AQDCe585Lnc", "Video"),
        ("Serious Cryptography – Free Sample Chapters", "https://nostarch.com/seriouscrypto", "Article"),
      ]),
      ("Penetration Testing Methodology", 4, [
        ("Full Ethical Hacking Course – freeCodeCamp", "https://www.youtube.com/watch?v=3Kq1MIfTWCE", "Video"),
        ("TryHackMe – SOC Level 1 Path (Free Tier)", "https://tryhackme.com/", "Course"),
      ]),
      ("Burp Suite & Web App Pentesting", 5, [
        ("Burp Suite Tutorial – TCM Security", "https://www.youtube.com/watch?v=G3hpAeoZ4ek", "Video"),
        ("PortSwigger Web Security Academy (Free)", "https://portswigger.net/web-security", "Course"),
      ]),
      ("Network Scanning — Nmap", 6, [
        ("Nmap Tutorial – NetworkChuck", "https://www.youtube.com/watch?v=4t4kBkMsDbQ", "Video"),
        ("Nmap Official Guide (Free Book)", "https://nmap.org/book/toc.html", "Article"),
      ]),
      ("Exploitation — Metasploit Framework", 7, [
        ("Metasploit Full Course – TCM Security", "https://www.youtube.com/watch?v=aEl-GrEBPik", "Video"),
        ("Metasploit Unleashed (Free)", "https://www.metasploitunleashed.com/", "Course"),
      ]),
      ("Digital Forensics & Incident Response", 8, [
        ("DFIR Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=8GqSAiMHRkA", "Video"),
        ("13Cubed – DFIR YouTube Channel", "https://www.youtube.com/@13Cubed", "Video"),
      ]),
    ]
  },
  {
    "title": "Data Engineer",
    "description": "Build the pipelines that power analytics at scale.",
    "nodes": [
      ("SQL Mastery & Window Functions", 1, [
        ("SQL Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=HXV3zeQKqGY", "Video"),
        ("Mode Analytics SQL Tutorial (Free)", "https://mode.com/sql-tutorial/", "Course"),
      ]),
      ("Python for Data Engineering", 2, [
        ("Python for Data Engineering – freeCodeCamp", "https://www.youtube.com/watch?v=W7QByFjVom8", "Video"),
        ("Kaggle Python Course (Free)", "https://www.kaggle.com/learn/python", "Course"),
      ]),
      ("Apache Spark & PySpark", 3, [
        ("PySpark Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=_C8kWso4ne4", "Video"),
        ("Apache Spark Docs – Getting Started", "https://spark.apache.org/docs/latest/quick-start.html", "Docs"),
      ]),
      ("Apache Kafka — Event Streaming", 4, [
        ("Kafka Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=SqVfCyfCJqw", "Video"),
        ("Confluent Kafka Tutorials (Free)", "https://developer.confluent.io/tutorials/", "Course"),
      ]),
      ("dbt — Data Build Tool", 5, [
        ("dbt Tutorial – freeCodeCamp", "https://www.youtube.com/watch?v=toSAAgLUHuk", "Video"),
        ("dbt Learn Courses (Free Tier)", "https://learn.getdbt.com/", "Course"),
      ]),
      ("Airflow — Workflow Orchestration", 6, [
        ("Apache Airflow Tutorial – Astronomer", "https://www.youtube.com/watch?v=IH1-0hwFZRQ", "Video"),
        ("Airflow Official Docs Tutorial", "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/index.html", "Docs"),
      ]),
      ("Data Modelling — Star Schema", 7, [
        ("Data Modelling for Beginners – freeCodeCamp", "https://www.youtube.com/watch?v=wOD02sezmX8", "Video"),
        ("Kimball Group Data Warehouse Toolkit (Free Preview)", "https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/", "Article"),
      ]),
    ]
  },
  {
    "title": "Android Developer",
    "description": "Native Android from zero to Play Store — Jetpack Compose & Kotlin.",
    "nodes": [
      ("Kotlin Language Fundamentals", 1, [
        ("Kotlin Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=F9UC9DY-vIU", "Video"),
        ("Kotlin Official Koans (Interactive)", "https://play.kotlinlang.org/koans/overview", "Course"),
      ]),
      ("Jetpack Compose — UI & Layouts", 2, [
        ("Jetpack Compose Course – Philipp Lackner", "https://www.youtube.com/playlist?list=PLQkwcJG4YTCSpJ2NLhDTHhi6XBNfk9WiC", "Video"),
        ("Official Compose Codelabs (Free)", "https://developer.android.com/courses/jetpack-compose/course", "Course"),
      ]),
      ("ViewModel & StateFlow", 3, [
        ("Android Architecture – Philipp Lackner", "https://www.youtube.com/watch?v=9sqvBydNJSg", "Video"),
        ("Android Architecture Guide (Official)", "https://developer.android.com/topic/architecture", "Docs"),
      ]),
      ("Retrofit & Ktor — Network Calls", 4, [
        ("Retrofit Tutorial – Traversy Media", "https://www.youtube.com/watch?v=t6Sql3WMAnk", "Video"),
        ("Ktor Client Docs (Free)", "https://ktor.io/docs/getting-started-ktor-client.html", "Docs"),
      ]),
      ("Room Database — Offline First", 5, [
        ("Room Database – Philipp Lackner", "https://www.youtube.com/watch?v=bOd3wO0uFr8", "Video"),
        ("Android Room with a View Codelab (Free)", "https://developer.android.com/codelabs/android-room-with-a-view-kotlin", "Course"),
      ]),
      ("Firebase — Auth, Firestore, FCM", 6, [
        ("Firebase for Android – Fireship", "https://www.youtube.com/watch?v=9kRgVxULbag", "Video"),
        ("Firebase Codelabs (Free)", "https://firebase.google.com/codelabs/firebase-android", "Course"),
      ]),
    ]
  },
  {
    "title": "iOS Developer",
    "description": "Ship beautiful Swift apps to the App Store using SwiftUI.",
    "nodes": [
      ("Swift Language Fundamentals", 1, [
        ("Swift Full Course – CodeWithChris", "https://www.youtube.com/watch?v=comQ1-x2a1Q", "Video"),
        ("Swift.org – A Swift Tour (Docs, Free)", "https://docs.swift.org/swift-book/documentation/the-swift-programming-language/guidedtour/", "Docs"),
      ]),
      ("SwiftUI — Views, State & Bindings", 2, [
        ("SwiftUI Masterclass – Hacking with Swift (Free)", "https://www.hackingwithswift.com/100/swiftui", "Course"),
        ("SwiftUI Tutorials – Apple Official", "https://developer.apple.com/tutorials/swiftui", "Docs"),
      ]),
      ("Async/Await & Structured Concurrency", 3, [
        ("Swift Concurrency – Hacking with Swift", "https://www.hackingwithswift.com/swift/5.5/async-await", "Article"),
        ("WWDC 2021 – Meet async/await in Swift (Free)", "https://developer.apple.com/videos/play/wwdc2021/10132/", "Video"),
      ]),
      ("Networking — URLSession & Combine", 4, [
        ("URLSession Tutorial – Paul Hudson", "https://www.hackingwithswift.com/books/ios-swiftui/using-urlsession-to-fetch-data", "Article"),
        ("Combine Framework – Sean Allen (YouTube)", "https://www.youtube.com/watch?v=MXW1lXqFBOQ", "Video"),
      ]),
      ("Core Data & SwiftData", 5, [
        ("Core Data Crash Course – CodeWithChris", "https://www.youtube.com/watch?v=O7u9nYWjvKk", "Video"),
        ("SwiftData Docs – Apple (Free)", "https://developer.apple.com/xcode/swiftdata/", "Docs"),
      ]),
    ]
  },
  {
    "title": "Blockchain & Web3 Developer",
    "description": "Smart contracts, DeFi, NFTs, and the decentralised web.",
    "nodes": [
      ("Blockchain Fundamentals & Consensus", 1, [
        ("Blockchain Explained – Savjee (Simply Explained)", "https://www.youtube.com/watch?v=SSo_EIwHSd4", "Video"),
        ("Bitcoin Whitepaper (Original, Free)", "https://bitcoin.org/bitcoin.pdf", "Article"),
      ]),
      ("Solidity — Smart Contract Language", 2, [
        ("Solidity Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=gyMwXuJrbJQ", "Video"),
        ("CryptoZombies – Learn Solidity (Free, Interactive)", "https://cryptozombies.io/", "Course"),
      ]),
      ("Hardhat / Foundry — Dev & Testing", 3, [
        ("Hardhat Full Tutorial – Patrick Collins", "https://www.youtube.com/watch?v=gyMwXuJrbJQ", "Video"),
        ("Hardhat Official Docs", "https://hardhat.org/docs", "Docs"),
      ]),
      ("ethers.js — Frontend Interaction", 4, [
        ("ethers.js Crash Course – Dapp University", "https://www.youtube.com/watch?v=a0osIaAOFSE", "Video"),
        ("ethers.js Docs (Free)", "https://docs.ethers.org/", "Docs"),
      ]),
      ("DeFi Protocols — Uniswap, Aave", 5, [
        ("DeFi MOOC – UC Berkeley (Free)", "https://defi-learning.org/f22", "Course"),
        ("Uniswap Docs – How Uniswap Works", "https://docs.uniswap.org/concepts/overview", "Docs"),
      ]),
      ("Security Auditing — Common Vulnerabilities", 6, [
        ("Smart Contract Security – Patrick Collins", "https://www.youtube.com/watch?v=_zf2OWerX0o", "Video"),
        ("Consensys Ethereum Smart Contract Security Best Practices", "https://consensys.github.io/smart-contract-best-practices/", "Article"),
      ]),
    ]
  },
]

# ─────────────────────────────────────────────────────────────────────────────
app = create_app()

with app.app_context():
    print("Truncating existing roadmap data (FK-safe)...")
    with db.engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        conn.execute(text("DELETE FROM node_resources"))
        conn.execute(text("DELETE FROM user_progress"))
        conn.execute(text("DELETE FROM roadmap_nodes"))
        conn.execute(text("DELETE FROM roadmaps"))
        conn.execute(text("PRAGMA foreign_keys = ON"))

    total_nodes = 0
    total_resources = 0

    for rm_data in ROADMAPS:
        rm = Roadmap(title=rm_data["title"], description=rm_data["description"])
        db.session.add(rm)
        db.session.flush()

        for (node_title, order_idx, resources) in rm_data["nodes"]:
            node = RoadmapNode(roadmap_id=rm.id, title=node_title, order_index=order_idx)
            db.session.add(node)
            db.session.flush()
            total_nodes += 1

            for (rtitle, rurl, rtype) in resources:
                db.session.add(NodeResource(node_id=node.id, title=rtitle, url=rurl, rtype=rtype))
                total_resources += 1

    db.session.commit()
    print(f"✅  Seeded {len(ROADMAPS)} roadmaps, {total_nodes} topics, {total_resources} free resource links.")
