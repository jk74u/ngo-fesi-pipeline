DevelopmentLog: Dissertation project of textual extraction and modelling of NGO info

7/8/26: Corpus assembly for NGO steel from 2006-2026 (adjustable) into 5 year time periods (adjustable). For now we would go for these numbers to start programming but making them adjustable helps if better time framing or analysis gap is required. 

Goal: For now we will build and develop corpus and then test it on the research papers we have gathered from out literature review as a test of the system working

Problems:

Next step: hopefully if this system works expanding the inputs through automated or manual means is another task entirely 

AI use: Claude structured what a build for this pipeline may look like i have discussed and traded ideas onto what are reasonable goals for today before it helps me with the coding process.
Concluding update: SETUP complete config setup corpus still needs building .

8/8/26: 40 pdf test passed.
core corpus logic completed tes was don with a temporary zotero csv to gather metadata but text extraction worked well with a slight test on tables which ran ok not guarnteed to always however.

10 attribute row decided each pdf has its own hashed id every stage having a clear error handaling and debugging setup with processed failed readings or missing information 

every stage was built so it was inspectable by me and checked that it gave a readable output searches pritns of text to read etc. 

system is built that every stage could be reused or replaced with a new tool e.g for now zotero metadata fro the pdfs we have however will have to eb replaced when automated new pdfs are handaled thorugh an api that does it as the source comes through.

validation of cross checking the actual pdfs against a zoetero record to encure ther was no missing files 

Problems: some text names were not consistent across actual pdf and zotero metadata. plus some pdf were missing its metadata that had to be handled mannually (short unwanted fix).
table data is flattend in order yes but falttened. will have to fix later stages of pipeline
Ai use: intructional guidance on how to code in desgin and discussion on the overall design of teh system including the way forward in building each section.