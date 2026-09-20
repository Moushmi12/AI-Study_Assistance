import streamlit as st
import pymupdf
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


# =====================================================
# API KEY
# =====================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# For Streamlit Cloud
if not API_KEY:
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
    except Exception:
        API_KEY = None

if not API_KEY:
    st.error("❌ Gemini API key not found!")
    st.info(
        "For local use, add GEMINI_API_KEY to .env. "
        "For Streamlit Cloud, add it in Secrets."
    )
    st.stop()

client = genai.Client(api_key=API_KEY)


# =====================================================
# PAGE SETTINGS
# =====================================================

st.set_page_config(
    page_title="AI Student Study Assistant",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI Student Study Assistant")

st.write(
    "Upload your study notes and learn any topic "
    "in an easy and exam-friendly way."
)


# =====================================================
# BASIC AI FUNCTION
# =====================================================

def ask_ai(prompt):

    models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash"
    ]

    last_error = None

    for model in models:

        try:

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            if response.text:
                return response

        except Exception as e:

            last_error = e

            error_text = str(e)

            # Retry only for temporary 503 errors
            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
            ):

                time.sleep(2)
                continue

            # Do not repeatedly retry quota errors
            raise e

    raise Exception(str(last_error))


# =====================================================
# WEB SEARCH AI FUNCTION
# =====================================================

def ask_ai_with_web(prompt):

    models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash"
    ]

    last_error = None

    for model in models:

        try:

            search_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

            config = types.GenerateContentConfig(
                tools=[search_tool]
            )

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )

            if response.text:
                return response

        except Exception as e:

            last_error = e

            error_text = str(e)

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
            ):

                time.sleep(2)
                continue

            raise e

    raise Exception(str(last_error))


# =====================================================
# PDF UPLOAD
# =====================================================

uploaded_file = st.file_uploader(
    "📄 Upload your study PDF",
    type=["pdf"]
)


# =====================================================
# PDF PROCESSING
# =====================================================

if uploaded_file:

    try:

        # Read uploaded PDF
        pdf_bytes = uploaded_file.read()

        document = pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        # =================================================
        # EXTRACT TEXT
        # =================================================

        text = ""

        for page in document:
            text += page.get_text()

        if not text.strip():

            st.error(
                "❌ Could not read text from this PDF."
            )

            st.stop()

        st.success(
            "✅ PDF uploaded successfully!"
        )

        st.info(
            f"📄 Number of pages: {len(document)}"
        )


        # =================================================
        # DETAILED SUMMARY
        # =================================================

        st.divider()

        st.header("📚 Detailed Summary")

        st.write(
            "Understand the complete topic in simple English."
        )

        if st.button("📚 Generate Detailed Summary"):

            summary_prompt = f"""
You are a friendly college teacher.

Read the uploaded study notes.

Create a detailed and easy-to-understand summary.

IMPORTANT RULES:

1. Use the uploaded notes as the main source.
2. Do not invent information.
3. Use simple English.
4. Cover important topics.
5. Explain difficult concepts simply.
6. Use headings and bullet points.
7. Explain processes step-by-step.
8. Give simple examples when useful.
9. Make it useful for exam preparation.
10. Keep the explanation clear and organized.

Use this structure:

# 📚 Detailed Summary

## Introduction

Explain the topic simply.

## Important Concepts

Explain the important concepts.

## How It Works

Explain processes step-by-step.

## Easy Example

Give an easy example if useful.

## Key Points

List the important points.

## Exam Points

Mention the important concepts
a student should remember for exams.

Uploaded Study Notes:

{text}
"""

            try:

                with st.spinner(
                    "🤖 Preparing detailed summary..."
                ):

                    response = ask_ai(
                        summary_prompt
                    )

                st.markdown(
                    response.text
                )

            except Exception as e:

                st.error(
                    "❌ Gemini API Error"
                )

                st.code(str(e))


        # =================================================
        # ASK ANYTHING
        # =================================================

        st.divider()

        st.header(
            "💬 Ask Anything From Your Notes"
        )

        st.write(
            "Ask any question. AI can use your notes "
            "and additional web information when useful."
        )

        question = st.text_input(
            "What do you want to know?",
            placeholder="Example: Explain Hadoop in detail"
        )


        # =================================================
        # ANSWER TYPE
        # =================================================

        answer_type = st.selectbox(
            "🎯 Choose answer type",
            [
                "Easy Explanation",
                "2 Mark Answer",
                "5 Mark Answer",
                "13 Mark Answer",
                "15 Mark Answer"
            ]
        )


        # =================================================
        # WEB SEARCH OPTION
        # =================================================

        use_web = st.checkbox(
            "🌐 Use additional web resources",
            value=False
        )


        # =================================================
        # EXPLAIN BUTTON
        # =================================================

        if st.button("🤖 Explain"):

            if not question.strip():

                st.warning(
                    "⚠️ Please enter your question."
                )

            else:

                # =================================================
                # ANSWER INSTRUCTIONS
                # =================================================

                if answer_type == "Easy Explanation":

                    instruction = """
Explain the topic in simple English.

Include:

- What it is
- Why it is used
- How it works
- Important points
- Easy example
- Easy way to remember
"""


                elif answer_type == "2 Mark Answer":

                    instruction = """
Give a short 2-mark exam-ready answer.

Include:

- Definition
- 1 or 2 important points

Keep it short, clear,
and easy to remember.
"""


                elif answer_type == "5 Mark Answer":

                    instruction = """
Give a 5-mark exam-ready answer.

Include:

1. Definition
2. Explanation
3. Important points
4. Example
5. Short conclusion

Make it clear and easy to understand.
"""


                elif answer_type == "13 Mark Answer":

                    instruction = """
Give a detailed 13-mark exam answer.

Use:

1. Introduction
2. Definition
3. Explanation
4. Components
5. Architecture if applicable
6. Working
7. Step-by-step process
8. Example
9. Advantages
10. Limitations
11. Applications
12. Key Points
13. Conclusion

Make it detailed but easy to understand.
Use headings and bullet points.
"""


                else:

                    instruction = """
Give a detailed 15-mark exam answer.

Use:

1. Introduction
2. Definition
3. Explanation
4. Components / Architecture
5. Working
6. Step-by-step process
7. Example
8. Advantages
9. Limitations
10. Applications
11. Key Points
12. Conclusion

Make it detailed, exam-oriented,
and easy to remember.

Use headings, bullet points,
and simple examples.
"""


                # =================================================
                # QUESTION PROMPT
                # =================================================

                question_prompt = f"""
You are an expert college teacher
and AI Student Study Assistant.

The student has uploaded study notes.

Student Question:

{question}

Answer Type:

{answer_type}

Answer Requirements:

{instruction}

IMPORTANT RULES:

1. Understand the uploaded study notes first.
2. Use the uploaded notes as the primary source.
3. If web resources are enabled,
   use reliable educational or official sources.
4. Do not invent information.
5. Explain in simple English.
6. Explain difficult words simply.
7. Give examples when useful.
8. Explain processes step-by-step.
9. Make the answer useful for exams.
10. Focus exactly on the student's question.
11. Do not create fixed questions.
12. The student decides what they want to learn.
13. If the answer is not available in the uploaded notes
    and web search is disabled, clearly say so.
14. Do not unnecessarily make the answer complicated.

If web information is used, clearly mention:

"Additional information from web resources"

Uploaded Study Notes:

{text}
"""


                # =================================================
                # GENERATE ANSWER
                # =================================================

                try:

                    with st.spinner(
                        "🤖 Preparing your answer..."
                    ):

                        if use_web:

                            response = ask_ai_with_web(
                                question_prompt
                            )

                        else:

                            response = ask_ai(
                                question_prompt
                            )


                    # =================================================
                    # DISPLAY ANSWER
                    # =================================================

                    st.subheader(
                        "🤖 Easy & Detailed Explanation"
                    )

                    st.markdown(
                        response.text
                    )


                    # =================================================
                    # DISPLAY WEB SOURCES
                    # =================================================

                    if use_web:

                        st.divider()

                        st.subheader(
                            "🔗 Sources Used"
                        )

                        try:

                            metadata = (
                                response.candidates[0]
                                .grounding_metadata
                            )

                            if (
                                metadata
                                and metadata.grounding_chunks
                            ):

                                source_found = False

                                for chunk in (
                                    metadata.grounding_chunks
                                ):

                                    if (
                                        chunk.web
                                        and chunk.web.uri
                                    ):

                                        source_found = True

                                        title = (
                                            chunk.web.title
                                            or "Web Source"
                                        )

                                        uri = chunk.web.uri

                                        st.markdown(
                                            f"- [{title}]({uri})"
                                        )

                                if not source_found:

                                    st.write(
                                        "No web sources were used."
                                    )

                            else:

                                st.write(
                                    "No web sources were used."
                                )

                        except Exception:

                            st.write(
                                "Source information is not available."
                            )


                except Exception as e:

                    error_text = str(e)

                    if (
                        "429" in error_text
                        or "RESOURCE_EXHAUSTED" in error_text
                    ):

                        st.error(
                            "⚠️ Gemini quota/rate limit reached."
                        )

                        st.info(
                            "Try again later or keep "
                            "Web Resources OFF."
                        )

                    else:

                        st.error(
                            "❌ Gemini API Error"
                        )

                    st.code(
                        error_text
                    )


        # =================================================
        # VIEW EXTRACTED PDF TEXT
        # =================================================

        with st.expander(
            "📄 View Extracted PDF Text"
        ):

            st.text_area(
                "PDF Text",
                text,
                height=300
            )


    except Exception as e:

        st.error(
            "❌ PDF processing error"
        )

        st.code(
            str(e)
        )
