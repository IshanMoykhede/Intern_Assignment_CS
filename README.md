Intern Assignment --- Document RAG Chatbot
A document question-answering API built with FastAPI, SQLite,
ChromaDB, Sentence Transformers, and Groq via LangChain.
Users can upload PDF, DOCX, or TXT documents, ask questions about
uploaded content, receive answers grounded in retrieved document chunks,
and delete a session with its related data.
Features
- Upload PDF, DOCX, and TXT files.
- Extract document text and split it into overlapping chunks.
- Generate embeddings using sentence-transformers/all-MiniLM-L6-v2.
- Store document chunks and metadata in ChromaDB.
- Retrieve the top five relevant chunks for a question, filtered by
  session.
- Generate context-grounded answers using Groq's openai/gpt-oss-120b
  model.
- Return source metadata: filename, page number, and chunk index.
- Save user questions and assistant answers in SQLite.
- Delete a session's chat history, document records, uploaded files,
  and ChromaDB chunks.
Architecture and workflow
Document ingestion
1. The client sends a document to POST /upload.
2. The API creates a session and saves the uploaded file under
   data/uploads/ using a generated filename.
3. Document metadata is saved in SQLite.
4. data_ingestion.py extracts text:
   - PDF: extracts text page by page with pypdf.
   - DOCX: extracts paragraphs with python-docx.
   - TXT: reads UTF-8 text.
5. RecursiveCharacterTextSplitter splits the text into chunks of
   1,000 characters with 200 characters of overlap.
6. The embedding model converts chunks to vectors.
7. ChromaDB stores the chunks and metadata, including session_id,
   document_id, filename, page, and chunk_index.
Question answering (RAG)
1. The client sends a session_id and question to POST /chat.
2. The API verifies that the session exists.
3. data_retrieval.py embeds the query and retrieves up to five
   semantically similar chunks from ChromaDB, filtered by session_id.
4. The retrieved chunks are included in a LangChain prompt.
5. Groq generates an answer using the supplied context. The prompt
   instructs the model not to invent facts and to say when the answer
   cannot be found.
6. The question and answer are saved in SQLite.
7. The API returns the answer and source metadata.
Session deletion
DELETE /sessions/{session_id} removes the session's ChromaDB chunks,
uploaded files, document records, chat messages, and session record.
Technology stack
- API: FastAPI, Uvicorn
- Relational storage: SQLite, SQLAlchemy
- Vector storage: ChromaDB
- Text extraction: pypdf, python-docx, Python file I/O
- Chunking: LangChain text splitters
- Embeddings: Hugging Face Sentence Transformers
  (all-MiniLM-L6-v2)
- LLM integration: LangChain Groq (openai/gpt-oss-120b)
- Configuration: python-dotenv
Project structure
intern_Assignment/
├── app/
│   ├── main.py
│   ├── routes/
│   │   ├── upload.py
│   │   ├── chat.py
│   │   └── deletesession.py
│   ├── services/
│   │   ├── data_ingestion.py
│   │   └── data_retrieval.py
│   ├── db/
│   │   └── database.py
│   └── models/
│       ├── session.py
│       ├── document.py
│       ├── chat.py
│       └── chat_request.py
├── data/
│   ├── uploads/
│   └── chroma/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
The exact tree may vary slightly as the project evolves.
Prerequisites
- Python installed
- A Groq API key
- Internet access for installing packages and downloading the
  embedding model on first use
Setup
1. Clone the repository
git clone https://github.com/IshanMoykhede/Intern_Assignment_CS.git
cd Intern_Assignment_CS
2. Create and activate a virtual environment
Windows PowerShell:
python -m venv venv
.\venv\Scripts\Activate.ps1
If PowerShell blocks activation, use the appropriate execution policy
for your machine or activate the environment from your IDE.
3. Install dependencies
python -m pip install -r requirements.txt
Ensure requirements.txt includes the packages used by the project,
including fastapi, uvicorn, sqlalchemy, python-multipart,
chromadb, langchain-text-splitters, pypdf, python-docx,
sentence-transformers, langchain-huggingface, langchain-chroma,
langchain-groq, and python-dotenv.
4. Configure environment variables
Copy .env.example to .env and replace the placeholder with your
actual key:
GROQ_API_KEY=your_actual_groq_api_key
Get a key from Groq Console. Never
commit .env or expose your API key.
5. Start the API
From the project root:
uvicorn app.main:app --reload
Open the interactive API documentation at:
http://127.0.0.1:8000/docs
The SQLite database (chatbot.db) and data directories are created/used
by the application as configured in the code.
API usage
1. Upload a document
Endpoint: POST /upload
In Swagger (/docs), expand the endpoint, choose a PDF, DOCX, or TXT
file, and execute the request.
Example successful response:
{
  "success": true,
  "session_id": "returned-session-id",
  "document_id": "returned-document-id",
  "filename": "resume.pdf",
  "chunks_stored": 8
}
Save the returned session_id. The current implementation creates a new
session for each upload.
2. Ask a question
Endpoint: POST /chat
Request body:
{
  "session_id": "returned-session-id",
  "question": "What skills are mentioned in the resume?"
}
Example response shape:
{
  "success": true,
  "session_id": "returned-session-id",
  "question": "What skills are mentioned in the resume?",
  "answer": "The answer generated from the retrieved document context.",
  "citations": [
    {
      "filename": "resume.pdf",
      "page": 1,
      "chunk_index": 0
    }
  ]
}
The answer and citation values above are illustrative. The actual result
depends on the uploaded document and retrieval results.
3. Delete a session
Endpoint: DELETE /sessions/{session_id}
Pass the session ID returned by /upload. This endpoint is intended to
delete the session and its associated chat records, document records,
uploaded files, and ChromaDB chunks.
Data storage
- SQLite (chatbot.db): sessions, document metadata, and chat
  messages.
- ChromaDB (data/chroma/): chunk text, vectors, and retrieval
  metadata.
- Uploaded files (data/uploads/): original uploaded documents.
SQLite and ChromaDB are separate stores; a deletion operation involving
both is not one atomic database transaction.
Current implementation notes
- Each upload creates a new session. Reusing an existing session for
  multiple uploads is not currently implemented.
- Chat messages are persisted, but previous messages are not yet added
  to the LLM prompt; conversational memory is not implemented.
- The chat endpoint returns metadata for retrieved chunks. These are
  retrieved-source citations, not a guarantee that the model relied on
  every listed chunk.
- Text extraction from DOCX and TXT assigns page number 1; those
  formats do not provide PDF-style page numbering in this
  implementation.
- Scanned/image-only PDFs may require OCR; current PDF extraction uses
  pypdf text extraction.
- The current implementation retrieves up to five chunks, but it does
  not apply an explicit relevance-score threshold.
- Do not upload sensitive documents to a hosted LLM unless you have
  permission and understand the provider's data-handling terms.
Troubleshooting
- ModuleNotFoundError: activate the correct virtual environment
  and install requirements again.
- GROQ_API_KEY missing or invalid: verify the .env file is in
  the project root and the key is valid.
- No relevant chunks found: verify that upload succeeded and that
  you are using the exact session_id returned for that upload.
- Embedding model download fails: check internet access and retry
  after connectivity is restored.
- Port already in use: stop the other server process or run
  Uvicorn on another port.
Security reminders
- Keep .env, venv/, chatbot.db, data/uploads/, and
  data/chroma/ out of version control.
- .env.example should contain placeholders only.
- Validate and limit upload sizes before deploying this API publicly.
- Configure CORS for trusted origins before production deployment.
License
Add the license required by your assignment or repository before
distributing the project.