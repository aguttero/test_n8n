import pymupdf

FOLDER_IN = "./file_in"
FOLDER_OUT = "./file_out" 

doc = pymupdf.open(f"{FOLDER_IN}/response with audit trail_v01.pdf") # open a document
out = open(f"{FOLDER_OUT}/JAD_AT_OUTPUT_v01.txt", "wb") # create a text output
for page in doc: # iterate the document pages
    text = page.get_text().encode("utf8") # get plain text (is in UTF-8)
    out.write(text) # write text of page
    out.write(bytes((12,))) # write page delimiter (form feed 0x0C)
out.close()