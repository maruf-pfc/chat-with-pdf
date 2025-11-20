(env) softvence@maruf:~/Documents/projects/github/chat-with-pdf/worker$ uvicorn main:app --reload --port 8000
INFO:     Will watch for changes in these directories: ['/home/softvence/Documents/projects/github/chat-with-pdf/worker']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [15884] using StatReload
INFO:     Started server process [15886]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:42758 - "POST /process-pdf HTTP/1.1" 200 OK
INFO:     127.0.0.1:43322 - "POST /ask HTTP/1.1" 200 OK

(env) softvence@maruf:~/Documents/projects/github/chat-with-pdf/worker$ docker compose down -v
[+] Running 3/3
 ✔ Container chatpdf-db           Removed                                   0.1s 
 ✔ Volume chat-with-pdf_db-data   Removed                                   0.0s 
 ✔ Network chat-with-pdf_default  Remove...                                 0.1s 
 
(env) softvence@maruf:~/Documents/projects/github/chat-with-pdf/worker$ docker compose up -d db
[+] Running 3/3
 ✔ Network chat-with-pdf_default  Create...                                 0.0s 
 ✔ Volume chat-with-pdf_db-data   Created                                   0.0s 
 ✔ Container chatpdf-db           Started                                   0.1s 
 
(env) softvence@maruf:~/Documents/projects/github/chat-with-pdf/worker$ docker compose exec db psql -U postgres -d postgres -c "\dt"
           List of relations
 Schema |   Name    | Type  |  Owner   
--------+-----------+-------+----------
 public | chunks    | table | postgres
 public | documents | table | postgres
 public | messages  | table | postgres
(3 rows)

(env) softvence@maruf:~/Documents/projects/github/chat-with-pdf/worker$ curl -X POST "http://localhost:8000/process-pdf" \
  -F "file=@./mvc.pdf"
{"message":"PDF processed successfully","document_id":1,"total_chunks":34}

(env) softvence@maruf:~/Documents/projects/github/chat-with-pdf/worker$ curl -Xcurl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"sess-123","question":"Explain MVC architecture?", "top_k":4}'
{"prompt":"SYSTEM: You are an AI assistant answering questions strictly using the retrieved documents. If unsure, say you are unsure. Cite evidence like [DOC 1].\n\nRELEVANT DOCUMENTS:\n[DOC 1] (doc=1 idx=33)\nof files and directories included in the project and any other references that reference other projects. The XLI 41 project file extension is determined by the programming language used to create the ASP.NET MVC Web application. The project file extension will be.ccsproj if you are using the C# programing lang. , and.vbproj if you are using the Visual Basic programming language. By default, the asp.net mvvc5 Web application creates and shows the following Folders and Files in Microsoft Visual Sstudio.Ssolution NET's Explorer window. The mvcc5 application's folders and files are listed below: ● Properties ● References ● App_Data ● App_Start ● Content ● Controllers ● Fonts ● Models ● Scripts ● Views ● Global.asax ● packages.config ● Web.Config XLII 42 REFERENCES: 1. Abdul Majeed, Ibtisam Rauf. MVC Architecture: A Detailed Insight to the Modern Web Applications Development. Peer Rev J Sol Photoen Sys .1(1). PRSP.000505. 2018. 2. Selfa DM, Carrillo M, Boone MDR (2006) A database and web application based on MVC architecture. 16th International Conference on Electronics, Communications and Computers (CONIELECOMP’06), p. 48. 3. Ahmed M, Uddin MM, Azad MS, Haseeb S (2010) MySQL performance analysis on a limited resource server. SpringSim 10 Proceedings of the 2010 Spring Simulation Multiconference, p. 1. 4. Stratmann E, Ousterhout J, Madan S (2011) Integrating long polling with an MVC framework. Stanford University, USA, p. 10. 5. Shu-qiang H, Huan-ming Z (2008) Research on improved MVC design pattern based on struts and XSL. 2008 International Symposium on Information Science and Engineering, pp. 451-455. XLIII 43 Plag\n\nCONVERSATION HISTORY:\nUSER: Explain MVC architecture?\n\nUSER QUESTION:\nExplain MVC architecture?\n\nINSTRUCTIONS: Answer using the documents above, cite [DOC X].","retrieved":[{"id":34,"document_id":1,"chunk_index":33,"text":"of files and directories included in the project and any other references that reference other projects. The XLI 41 project file extension is determined by the programming language used to create the ASP.NET MVC Web application. The project file extension will be.ccsproj if you are using the C# programing lang. , and.vbproj if you are using the Visual Basic programming language. By default, the asp.net mvvc5 Web application creates and shows the following Folders and Files in Microsoft Visual Sstudio.Ssolution NET's Explorer window. The mvcc5 application's folders and files are listed below: ● Properties ● References ● App_Data ● App_Start ● Content ● Controllers ● Fonts ● Models ● Scripts ● Views ● Global.asax ● packages.config ● Web.Config XLII 42 REFERENCES: 1. Abdul Majeed, Ibtisam Rauf. MVC Architecture: A Detailed Insight to the Modern Web Applications Development. Peer Rev J Sol Photoen Sys .1(1). PRSP.000505. 2018. 2. Selfa DM, Carrillo M, Boone MDR (2006) A database and web application based on MVC architecture. 16th International Conference on Electronics, Communications and Computers (CONIELECOMP’06), p. 48. 3. Ahmed M, Uddin MM, Azad MS, Haseeb S (2010) MySQL performance analysis on a limited resource server. SpringSim 10 Proceedings of the 2010 Spring Simulation Multiconference, p. 1. 4. Stratmann E, Ousterhout J, Madan S (2011) Integrating long polling with an MVC framework. Stanford University, USA, p. 10. 5. Shu-qiang H, Huan-ming Z (2008) Research on improved MVC design pattern based on struts and XSL. 2008 International Symposium on Information Science and Engineering, pp. 451-455. XLIII 43 Plag","score":0.4388390779495239}],"session_id":"sess-123"}

(env) softvence@maruf:~/Documents/projects/github/chat-with-pdf/worker$ 
