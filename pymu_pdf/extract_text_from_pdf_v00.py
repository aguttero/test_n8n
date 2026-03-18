#import pymupdf
import pymupdf4llm, json

FOLDER_IN = "./file_in"
FOLDER_OUT = "./file_out" 

# doc = pymupdf.open(f"{FOLDER_IN}/response with audit trail_v01.pdf") # open a document
# out = open(f"{FOLDER_OUT}/JAD_AT_OUTPUT_v01.txt", "wb") # create a text output
# for page in doc: # iterate the document pages
#     text = page.get_text().encode("utf8") # get plain text (is in UTF-8)
#     out.write(text) # write text of page
#     out.write(bytes((12,))) # write page delimiter (form feed 0x0C)
# out.close()


# LLM as JSON
# json_data = pymupdf4llm.to_json(f"{FOLDER_IN}/response with audit trail_v01.pdf")

# with open (f"{FOLDER_OUT}/JAD_AT_OUTPUT_LLM_v01.json", "w") as file:
#     json.dump(json_data, file, ensure_ascii=False, indent=4)

# LLM as MD
md = pymupdf4llm.to_markdown(f"{FOLDER_IN}/response with audit trail_v01.pdf")

with open (f"{FOLDER_OUT}/JAD_AT_OUTPUT_LLM_v01.md", "w", encoding="utf-8") as file:
    file.write (md)


# LLM as TXT
txt = pymupdf4llm.to_text(f"{FOLDER_IN}/response with audit trail_v01.pdf")

with open (f"{FOLDER_OUT}/JAD_AT_OUTPUT_LLM_v01.txt", "w", encoding="utf-8") as file:
    file.write (txt)



