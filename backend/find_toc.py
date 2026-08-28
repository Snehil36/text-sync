from google import genai
from google.genai import types
import pymupdf
import os


def find_toc(pdf_path):

    # FORCE USE OF GLOBAL GOOGLE SERVERS: Stops the SDK from detecting AWS 
    # environment variables and generating a corrupt cloud network path.
    # uses HTTP Option object class to prevent python from crashing on setup
    client = genai.Client(api_key=os.getenv("PDF_OFFSETTER"),
                          http_options=types.HttpOptions(api_version='v1',
                          timeout=120000 # gives 120 seconds for pdf uploading
                          )
                        )   
                    
    doc = pymupdf.open(pdf_path)

    # Incase pdf is over the max page size of 100 just takes first 50
    condensed_doc = pymupdf.open()
    condensed_doc.insert_pdf(doc, from_page=0, to_page=49)
    condensed_doc.save("temp_first50.pdf")

    file = client.files.upload(file="temp_first50.pdf")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            file,
            """You are a PDF analysis tool. Analyze this PDF and find the table of contents.
            Return ONLY a valid JSON object with no markdown, no code blocks, no explanation, no extra text.
            The JSON must follow this exact format:

            {
                "first_chapter_printed_page": <the printed page number of the first chapter>,
                "first_chapter_pdf_page": <the actual PDF page number where the first chapter starts>,
                "toc": {
                    "<exact chapter title>": <printed page number>
                }
            }

            Rules:
            - Return JSON only, nothing else
            - Do not wrap in markdown or code blocks
            - Include every chapter and section in the toc
            - Use the printed page numbers from the table of contents, not PDF page numbers
            """
        ]
    )
    os.remove("temp_first50.pdf")
    return response.text