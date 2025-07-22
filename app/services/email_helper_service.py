import sqlite3
import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class EmailHelperService:
    """Service for the Email Learning Assistant chatbot"""

    def __init__(self):
        # Load environment variables
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'helper_bot', 'email_faq.db')

    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_answer(self, user_question: str, language_code: str = 'en') -> str:
        """Get answer from database or AI"""
        answer = None
        conn = None

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Try exact match first
            cursor.execute("SELECT answer FROM email_faq WHERE LOWER(question) = ?",
                         (user_question.lower(),))
            result = cursor.fetchone()

            if result:
                answer = result["answer"]
                logger.info(f"✅ Answer from database: {answer}")
            else:
                # Try partial match
                cursor.execute("SELECT question, answer FROM email_faq WHERE LOWER(question) LIKE ?",
                             (f'%{user_question.lower()}%',))
                results = cursor.fetchall()

                if results:
                    # Return the first matching result
                    answer = results[0]["answer"]
                    logger.info(f"✅ Partial match from database: {answer}")
                else:
                    # Fall back to AI
                    if self.client:
                        answer = self._get_ai_answer(user_question, language_code)
                    else:
                        answer = "I'm sorry, I don't have information about that specific topic. Please check the email classification system documentation or contact support."

            # Save the interaction
            cursor.execute("INSERT INTO email_faq (question, answer) VALUES (?, ?)",
                         (user_question, answer))
            conn.commit()
            logger.info("💾 Interaction saved to database")

        except sqlite3.Error as e:
            logger.error(f"❌ Database Error: {str(e)}")
            answer = "Database error occurred. Please try again."
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            answer = f"An unexpected error occurred: {str(e)}"
        finally:
            if conn:
                conn.close()

        return answer

    def _get_ai_answer(self, user_question: str, language_code: str) -> str:
        """Get answer from OpenAI with formatting instructions"""
        try:
            system_prompt = f"""You are Mike's Email Classification System Learning Assistant.
            Help users understand and use the email classification, sorting, and management features.

            FORMATTING INSTRUCTIONS:
            - Use **bold** for important terms and headings
            - Use *italics* for emphasis
            - Use `code` for UI elements, buttons, and technical terms
            - Use ### for section headings
            - Use numbered lists (1. 2. 3.) for step-by-step instructions
            - Use bullet points (- or •) for feature lists
            - Include relevant emojis for visual appeal
            - Format priority levels as **Critical**, **High**, **Medium**, **Low**

            You can help with:
            - How to use the email classifier and sorter
            - Understanding email categories (**Critical Alerts**, **New Leads**, **Maintenance Requests**, **Offers & Contracts**, **Tenant Communications**)
            - Priority levels (**Critical**, **High**, **Medium**, **Low**)
            - Using the dashboard features
            - Managing email workflows
            - Troubleshooting common issues
            - Best practices for email organization

            Reply professionally in {language_code} language. Keep responses concise and practical.
            Always format your response for better readability."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                max_tokens=500,  # Increased for formatted responses
                temperature=0.7,
            )
            answer = response.choices[0].message.content.strip()
            logger.info(f"🤖 Answer from AI: {answer}")
            return answer

        except Exception as e:
            logger.error(f"❌ AI Error: {str(e)}")
            return "I'm having trouble accessing my AI knowledge right now. Please try again later or contact support."