import streamlit as st
import pandas as pd
import io
import requests
import json
import time

# --- Helper Function to create sample Excel files in memory ---
def create_sample_files():
    """Creates two sample Excel files (scores and comments) in memory for download."""
    
    # Sample Data for Scores
    scores_data = {
        'name': ['Ayesha', 'Ali', 'Badreyah'],
        'gender': ['Female', 'Male', 'Female'],
        'level': ['Guide', 'Apply', 'Apply'],
        'Overall Leadership': [2.97, 2.55, 3.66],
        'Drives Results': [3.0, 1.9, 3.9],
        'Leads People': [3.2, 2.6, 4.2],
        'Manages Stakeholders': [2.4, 2.4, 4.2],
        'Thinks Strategically': [3.4, 2.5, 3.9],
        'Solves Challenges': [3.9, 1.7, 3.9],
        'Steers Change': [2.9, 2.8, 4.3]
    }
    scores_df = pd.DataFrame(scores_data)

    # Sample Data for Assessor Comments
    comments_data = [
        {'name': 'Ayesha', 'comment_type': 'Strength', 'Steers Change': 'The candidate demonstrates confidence in navigating periods of change and serves as a role model, creating a positive attitude during change initiatives.', 'Manages Stakeholders': 'The candidate demonstrates effective strategies for identifying relationships that can support the achievement of their individual objectives.', 'Drives Results': 'The candidate demonstrates a committed approach to maintaining consistent performance for themselves and their team across projects.', 'Thinks Strategically': 'The candidate demonstrates a solid understanding of both short-term and long-term strategic approaches to projects.', 'Solves Challenges': 'The candidate demonstrates strong ability to identify issues proactively and develop effective, logical solutions.', 'Leads People': 'The candidate demonstrates the ability to support their team through valuable contributions that aid in the development of team members.'},
        {'name': 'Ayesha', 'comment_type': 'Development Area', 'Steers Change': 'The candidate would benefit from proactively seeking to understand the underlying reasons for change, to better sustain team motivation and engagement throughout the change process.', 'Manages Stakeholders': 'The candidate would benefit from ensuring that the mutual objectives of relevant stakeholders are aligned and supported, to secure buy-in and sustain long-lasting relationships.', 'Drives Results': 'The candidate would benefit from developing strategies to effectively allocate resources to address the varying priorities within the workload.', 'Thinks Strategically': 'The candidate would benefit from proactively anticipating external industry changes and adjusting plans accordingly to stay ahead of emerging trends.', 'Solves Challenges': 'The candidate would benefit from offering reassurance to team members during challenges and promoting resilience within the team.', 'Leads People': 'The candidate would benefit from effectively resolving conflicts within the team to maintain cohesion and a positive working environment.'},
        {'name': 'Ali', 'comment_type': 'Strength', 'Steers Change': 'The candidate evidenced being able to effectively navigate ambiguous situations by adapting to task changes.', 'Manages Stakeholders': 'The candidate demonstrates a solid ability to build relationships with key stakeholders within their environment.', 'Drives Results': 'The candidate demonstrates some ability to monitor their performance daily, which can support goal achievement', 'Thinks Strategically': 'The candidate demonstrates moderate awareness of risk factors that could delay project work and proactively seeks support to develop contingency plans.', 'Solves Challenges': 'The candidate demonstrates initiative in addressing project challenges and effectively raises issues with relevant stakeholders', 'Leads People': 'The candidate demonstrates reasonable confidence in collaborating effectively with others to achieve team objectives.'},
        {'name': 'Ali', 'comment_type': 'Development Area', 'Steers Change': 'The candidate would benefit by following up on actions to ensure change efforts are successful.', 'Manages Stakeholders': 'To strengthen this area, the candidate should allocate additional time to understand the interests and priorities of other stakeholders, to help create win-win situations.', 'Drives Results': 'The candidate provided limited evidence of exceeding goals and would benefit from developing strategies to consistently perform at or above higher-than-expected levels.', 'Thinks Strategically': 'The candidate should work on effectively proposing strategic recommendations that support team growth and long-term success.', 'Solves Challenges': 'The candidate should work on maintaining composure when faced with significant setbacks, to prevent becoming overwhelmed and to better manage challenges.', 'Leads People': 'The candidate would benefit from developing skills to manage disagreements within the team more effectively, ensuring that conflicts do not hinder project progress.'}
    ]
    comments_df = pd.DataFrame(comments_data)

    # Convert DataFrames to Excel format in memory
    output_scores = io.BytesIO()
    with pd.ExcelWriter(output_scores, engine='xlsxwriter') as writer:
        scores_df.to_excel(writer, index=False, sheet_name='Scores')
    processed_scores = output_scores.getvalue()

    output_comments = io.BytesIO()
    with pd.ExcelWriter(output_comments, engine='xlsxwriter') as writer:
        comments_df.to_excel(writer, index=False, sheet_name='Comments')
    processed_comments = output_comments.getvalue()
    
    return processed_scores, processed_comments

# --- Function to call Gemini API with exponential backoff ---
def call_gemini_api(prompt, api_key):
    """Calls the Gemini API with exponential backoff and returns the generated text."""
    if not api_key:
        return "Error: Gemini API key is missing. Please provide it in the sidebar."

    model_name = "gemini-2.5-flash-preview-05-20"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    max_retries = 5
    base_delay = 1  # seconds

    for i in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and result['candidates']:
                content_part = result['candidates'][0].get('content', {}).get('parts', [{}])[0]
                return content_part.get('text', "Error: Could not extract text from API response.")
            else:
                # Log the invalid response for debugging
                st.write(f"Invalid API response received: {result}")
                return f"Error: The API response was invalid."

        except requests.exceptions.RequestException as e:
            if i < max_retries - 1:
                time.sleep(base_delay * (2 ** i))
                continue
            else:
                return f"Error: An API request failed after multiple retries: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

# --- Main Application Logic ---
st.set_page_config(layout="wide", page_title="Leadership Report Generator")

st.title("🤖 Leadership Potential Report Generator")
st.markdown("""
This application uses Gemini to generate Leadership Potential Reports for all candidates in your uploaded files.
The final output will be a single Excel file containing all the generated summaries.
""")

# --- Sidebar for Uploads and Downloads ---
with st.sidebar:
    st.header("Setup & Configuration")
    
    # API Key Input
    st.subheader("1. Enter API Key")
    gemini_api_key = st.text_input("Gemini API Key", type="password", help="Get your key from Google AI Studio.")

    st.divider()

    # Download Sample Files
    st.subheader("2. Download Templates")
    sample_scores_data, sample_comments_data = create_sample_files()
    st.download_button(
        label="Download Scores Template (.xlsx)",
        data=sample_scores_data,
        file_name="sample_scores.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.download_button(
        label="Download Comments Template (.xlsx)",
        data=sample_comments_data,
        file_name="sample_comments.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()

    # File Uploaders
    st.subheader("3. Upload Your Files")
    uploaded_scores_file = st.file_uploader("Upload Candidate Scores Excel File", type=["xlsx"])
    uploaded_comments_file = st.file_uploader("Upload Assessor Comments Excel File", type=["xlsx"])

# --- Main Panel for Report Generation ---
if uploaded_scores_file and uploaded_comments_file:
    try:
        scores_df = pd.read_excel(uploaded_scores_file)
        comments_df = pd.read_excel(uploaded_comments_file)

        st.header("Generate All Summaries")
        st.info(f"Found **{len(scores_df['name'].unique())}** candidates in the uploaded files. Click the button below to generate all reports.")
        
        if st.button("✨ Generate All Summaries", type="primary"):
            if not gemini_api_key:
                st.error("Please enter your Gemini API key in the sidebar to proceed.")
            else:
                all_summaries = []
                candidate_list = scores_df['name'].unique()
                progress_bar = st.progress(0)
                
                for i, candidate_name in enumerate(candidate_list):
                    with st.spinner(f"Generating report for {candidate_name} ({i+1}/{len(candidate_list)})..."):
                        
                        # --- Data Preparation ---
                        candidate_data = scores_df[scores_df['name'] == candidate_name].iloc[0].to_dict()
                        strength_comments = comments_df[(comments_df['name'] == candidate_name) & (comments_df['comment_type'] == 'Strength')].iloc[0].to_dict()
                        dev_comments = comments_df[(comments_df['name'] == candidate_name) & (comments_df['comment_type'] == 'Development Area')].iloc[0].to_dict()

                        # --- Master Prompt ---
                        master_prompt = """
You are an expert talent management consultant. Your task is to generate a concise and insightful leadership potential summary based on a candidate's assessment data. The output must be professional, behavioral, and strictly adhere to the format and rules outlined in the Appendix.

First, learn from these high-quality examples (golden standards):

---
**EXAMPLE 1**
* **INPUT DATA:**
    * First Name: Ayesha, Gender: Female, Level: Guide
    * Scores: Overall Leadership: 2.97, Drives Results: 3.0, Leads People: 3.2, Manages Stakeholders: 2.4, Thinks Strategically: 3.4, Solves Challenges: 3.9, Steers Change: 2.9
    * Strength Comment (Solves Challenges): The candidate demonstrates strong ability to identify issues proactively and develop effective, logical solutions.
    * Strength Comment (Thinks Strategically): The candidate demonstrates a solid understanding of both short-term and long-term strategic approaches to projects.
    * Development Comment (Manages Stakeholders): The candidate would benefit from ensuring that the mutual objectives of relevant stakeholders are aligned and supported, to secure buy-in and sustain long-lasting relationships.
    * Development Comment (Steers Change): The candidate would benefit from proactively seeking to understand the underlying reasons for change, to better sustain team motivation and engagement throughout the change process.
* **CORRECT OUTPUT:**
    Ayesha demonstrates average potential for growth and success in a more complex role. A confident and resilient problem-solver, she navigates ambiguity well and shows an awareness of the bigger picture. While she is adaptable to change and supports others' development, her drive to achieve goals can be inconsistent, and she may need support to remain decisive during uncertainty. Her primary development area is in stakeholder engagement, where she would benefit from building stronger, more collaborative relationships.

    **Strengths:**
    * Demonstrates strong ability to identify issues proactively and develop effective, logical solutions.
    * Demonstrates a solid understanding of both short-term and long-term strategic approaches to projects.

    **Development Areas:**
    * Could benefit from ensuring that the mutual objectives of relevant stakeholders are aligned and supported, to secure buy-in and sustain long-lasting relationships.
    * Would benefit from proactively seeking to understand the underlying reasons for change to better sustain team motivation.
---
**EXAMPLE 2**
* **INPUT DATA:**
    * First Name: Badreyah, Gender: Female, Level: Apply
    * Scores: Overall Leadership: 3.66, Drives Results: 3.9, Leads People: 4.2, Manages Stakeholders: 4.2, Thinks Strategically: 3.9, Solves Challenges: 3.9, Steers Change: 4.3
    * Strength Comment (Steers Change): The candidate demonstrated strong comfort with changing environments and is supportive of adopting change initiatives.
    * Strength Comment (Leads People): The candidate demonstrates high effectiveness in collaborating with the team to develop solutions and achieve shared goals.
    * Development Comment (Thinks Strategically): Minimal development could be orientated towards improving task prioritization and effectively allocating workload to focus on strategically important activities.
    * Development Comment (Manages Stakeholders): Minor development could be focused on developing strategies to maintain key relationships over the long term that support sustained business outcomes.
* **CORRECT OUTPUT:**
    Badreyah demonstrates high potential for growth and success in a more complex role. She excels in changing and complex environments, showing great adaptability and decisiveness. A natural leader, she inspires others and builds strong, trust-based relationships while focusing on team development. Badreyah consistently demonstrates high motivation to achieve results, approaches her work with a strategic focus on the bigger picture, and solves challenges with confidence. Her development can focus on scaling these impressive strengths for even greater complexity.

    **Strengths:**
    * Demonstrated strong comfort with changing environments and is supportive of adopting change initiatives.
    * Demonstrates a high level of confidence in building relationships and understanding the needs of others.

    **Development Areas:**
    * Development could be orientated towards improving task prioritization and effectively allocating workload to focus on strategically important activities.
    * Could focus on developing strategies to maintain key relationships over the long term that support sustained business outcomes.
---

Now, using the rules and interpretation matrices in the Appendix below, generate a report for the new candidate data provided.

**CANDIDATE DATA TO PROCESS:**

* **First Name:** {name}
* **Gender:** {gender}
* **Level:** {level}
* **Scores:**
    * Overall Leadership: {Overall Leadership}
    * Drives Results: {Drives Results}
    * Leads People: {Leads People}
    * Manages Stakeholders: {Manages Stakeholders}
    * Thinks Strategically: {Thinks Strategically}
    * Solves Challenges: {Solves Challenges}
    * Steers Change: {Steers Change}
* **Assessor Strength Comments:**
    * Drives Results: {s_Drives Results}
    * Leads People: {s_Leads People}
    * Manages Stakeholders: {s_Manages Stakeholders}
    * Thinks Strategically: {s_Thinks Strategically}
    * Solves Challenges: {s_Solves Challenges}
    * Steers Change: {s_Steers Change}
* **Assessor Development Area Comments:**
    * Drives Results: {d_Drives Results}
    * Leads People: {d_Leads People}
    * Manages Stakeholders: {d_Manages Stakeholders}
    * Thinks Strategically: {d_Thinks Strategically}
    * Solves Challenges: {d_Solves Challenges}
    * Steers Change: {d_Steers Change}

---
### APPENDIX: RULES AND MATRICES

#### 1. Output Structure
Your final output must contain two parts:
1.  **Summary Paragraph:** A single paragraph of approximately 150 words.
2.  **Bulleted Points:** Two strengths and two development areas, each as a single-sentence bullet point.

#### 2. Generation Process and Rules
Follow this sequential process precisely.

* **Step 1: The Opening Sentence**
    Begin the summary paragraph with the sentence that corresponds exactly to the candidate's **Overall Leadership** score, using the "Overall Leadership Potential Matrix" below. Use the candidate's first name.

* **Step 2: The Summary Paragraph Narrative**
    After the opening sentence, construct a narrative paragraph by performing the following:
    * Identify the candidate's **Level** (Apply, Guide, or Shape) to select the correct interpretation matrix.
    * Identify the 2-3 highest-scoring and 2-3 lowest-scoring of the six core competencies.
    * Weave a narrative that describes the candidate's profile. Start with the themes from the highest-scoring competencies, followed by the lower-scoring areas to provide a balanced view.
    * For each competency described, use the **exact wording** from the corresponding interpretation matrix. Do not name the competencies.
    * **Crucially, conclude the paragraph by explicitly identifying the primary development area(s).** For most profiles, use phrases like 'Her primary development area is...' or 'His development can focus on...'. For high-performing candidates with all high scores, frame this positively, such as 'Her development can focus on scaling these impressive strengths for even greater complexity.'
    * Ensure the paragraph flows naturally. The entire paragraph must be approximately 150 words.

* **Step 3: Bullet Point Selection**
    * **Strengths:** Identify the two highest-scoring of the six core competencies. If there is a tie, select the competency with the most specific and behavioral **strength comment** from the assessor notes. Scores of 3.5 or above are always considered strengths.
    * **Development Areas:** Identify the two lowest-scoring of the six core competencies. Scores of 2.49 or below are always considered development areas. If all scores are high (e.g., above 3.5), select the two competencies with the relatively lowest scores. If assessor comments are minimal for the lowest score, you may select the next lowest score if its comment is more specific and actionable.

* **Step 4: Bullet Point Writing**
    * For each of the four selected competencies, use the corresponding **assessor comment** as your source.
    * Rephrase the assessor comment into a single, concise, behavioral sentence. For strengths, use the "Strengths" comment. For development areas, use the "Development Areas" comment.
    * The bullet points must provide specific behavioral evidence and should not be general statements.

#### 3. Writing Style and Constraints
* **Tone:** Neutral, professional, objective, and behavioral.
* **Voice:** Third person, present tense only (e.g., "She demonstrates," "He approaches").
* **Language:** American English.
* **Forbidden Terms:** Do not use the names of the competencies (e.g., "Drives Results"). Do not mention scores, numbers, AI, assessments, tools, or the assessment experience. Avoid vague or judgmental words like "good," "poor," "struggles," "strong," or "weak," unless they are part of the required interpretation text.
* **Pronouns:** Use the candidate's correct gender pronouns.

#### 4. Interpretation Matrices

**Overall Leadership Potential Matrix**
| Score Range | Interpretation |
| :--- | :--- |
| 3.50 - 5.00 | [First Name] demonstrates high potential for growth and success in a more complex role. |
| 3.00 - 3.49 | [First Name] demonstrates above average potential for growth and success in a more complex role. |
| 2.50 - 2.99 | [First Name] demonstrates average potential for growth and success in a more complex role. |
| 1.00 - 2.49 | [First Name] demonstrates low potential for growth and success in a more complex role. |

---

**"APPLY" Level Interpretation Matrix**
| Competency | High (3.5-5.0) | Moderate (2.5-3.49) | Low (1.0-2.49) |
| :--- | :--- | :--- | :--- |
| **Drives Results** | Consistently demonstrates high motivation and initiative to exceed expectations. A strong drive to achieve goals, targets, and results. Seeks fulfillment through impact. Drives a high-performance culture across teams and demonstrates grit and persistence when working toward ambitious targets. | Demonstrates motivation and takes initiative occasionally. Demonstrates a drive to achieve goals, but may need support. Interest in making an impact is present but not sustained. Moderate ability to articulate performance standards that contribute to achieving organisational goals. Occasionally supports performance across teams and shows persistence when working towards goals. | Demonstrates limited motivation or initiative; may meet expectations but does not show a consistent drive to exceed them. Fulfillment from work or desire to make an impact is not clearly evident. Low ability to articulate performance standards that support organisational goals. Needs development in fostering a high-performance culture and in maintaining persistence when faced with challenging goals. |
| **Leads People** | Consistently takes time to focus on both personal and professional growth - for both self and others. Actively pursues continuous improvement and excellence; shows clear willingness to learn and unlearn. Strongly supports development of others by identifying and leveraging individual strengths. Advocates for learning and career growth, contributing to a culture of learning and continuous improvement. | Focuses on personal and professional growth for self and others and engages in learning activities but may not do so consistently. Displays willingness to learn and unlearn. Recognizes others’ development needs and offers support, though may not consistently nurture growth or advocate for talent advancement. | Rarely focuses on personal or professional growth- for both self and others. Engagement in learning is limited and may resist feedback or change. Shows minimal interest in developing others or contributing to a learning environment. May neglect or avoid growth conversations. |
| **Manages Stakeholders**| Consistently shows capability to lead and inspire others. Displays strong empathy, understanding, and a focus on people. Builds relationships with ease and enjoys social interaction. Demonstrates strong ability to engage key stakeholders, build trust-based relationships, and find synergies for mutual outcomes. Proactively networks and stays connected across internal and external touchpoints. | Displays some ability to lead and inspire others. May show empathy and focus on people inconsistently. Moderate ability to maintain and build relationships with key stakeholders. Often identifies synergies for positive outcomes. Occasionally proactively networks. | Demonstrates limited capability in leading or inspiring others. Social interaction may be minimal or strained. Struggles to build and maintain relationships. Rarely engages with stakeholders and does not leverage relationships for mutual outcomes. Limited presence in networks or cross-functional collaboration. |
| **Thinks Strategically**| Approaches work with a strong focus on the bigger picture. Operates independently with minimal guidance. Demonstrates a commercial and strategic mindset, regularly anticipating trends and their impact. Effectively balances short-term goals with long-term organizational value. Translates complex goals into clear team actions and helps others understand broader implications. | Demonstrates some awareness of the bigger picture but may need occasional guidance. Understands strategy in parts but may not consistently anticipate trends or broader implications. Occasionally translates organisational goals into meaningful actions. Can focus on both immediate and longer-term needs but may favor one over the other. | Focus tends to be on immediate tasks. Requires frequent guidance. Displays limited awareness of trends or the strategic impact of work. Needs ongoing guidance to connect work with strategic direction. Struggles to translate organizational priorities into meaningful tasks or influence direction. |
| **Solves Challenges** | Consistently addresses problems and challenges with confidence and resilience. Takes a diligent, practical, and solution-focused approach. Comfortable navigating ambiguity and complexity. Makes sound decisions under pressure and thrives in environments with multiple demands. | Has the ability to address problems but may need time or support to build confidence and resilience. Attempts a practical approach but not always solution-focused. Moderate ability to handle ambiguity and complex envrionments. Shows some confidence in leading through uncertain environments. | Struggles to address problems confidently. May rely heavily on others. Practical or solution-oriented approaches are limited. Avoids complexity and ambiguity. Rarely takes initiative in resolving obstacles. |
| **Steers Change** | Thrives in change and complexity. Manages new ways of working with adaptability, flexibility, and decisiveness during change. Plays an active role in transformation initiatives, shows strong resilience, and enables buy-in and alignment from others during change. | Demonstrates ability to cope with change and can adapt when needed. May need support to remain flexible or decisive in uncertain situations. Contributes to organisational change initiatives, may enable buy-in and shows resilience during challenging times. | Struggles with change or uncertainty. May resist new ways of working and has difficulty adapting or deciding in changing circumstances. Rarely contributes to transformation efforts and finds it difficult to stay resilient under shifting demands. Has difficulty enabling buy-in and support. |

---

**"GUIDE" Level Interpretation Matrix**
| Competency | High (3.5-5.0) | Moderate (2.5-3.49) | Low (1.0-2.49) |
| :--- | :--- | :--- | :--- |
| **Drives Results** | Consistently demonstrates high motivation and initiative to exceed expectations. A strong drive to achieve goals, targets, and results. Seeks fulfillment through impact. Supports and guides team to deliver goals on time. Recognizes high performance, addresses underperformance, displays grit, and manages resources effectively. | Demonstrates motivation and takes initiative occasionally. Demonstrates a drive to achieve goals, but may need support. Interest in making an impact is present but not sustained. Supports team delivery but may need prompting. Occasionally recognizes performance and addresses underperformance. Shows some grit and manages resources with support. | Demonstrates limited motivation or initiative; may meet expectations but does not show a consistent drive to exceed them. Fulfillment from work or desire to make an impact is not clearly evident. Limited support for team delivery. Rarely recognizes performance or addresses underperformance. Struggles with grit and resource management. |
| **Leads People** | Consistently takes time to focus on both personal and professional growth - for both self and others. Actively pursues continuous improvement and excellence; shows clear willingness to learn and unlearn. Coaches key talent with timely, constructive feedback. Builds capability by offering challenging development opportunities. | Focuses on personal and professional growth for self and others and engages in learning activities but may not do so consistently. Displays willingness to learn and unlearn. Provides feedback and guidance, though not always timely or targeted. Offers some development opportunities, but impact may vary. | Rarely focuses on personal or professional growth- for both self and others. Engagement in learning is limited and may resist feedback or change. Rarely provides meaningful feedback or development. Struggles to coach talent or build individual capability. |
| **Manages Stakeholders**| Consistently shows capability to lead and inspire others. Displays strong empathy, understanding, and a focus on people. Builds relationships with ease and enjoys social interaction. Builds strong relationships to achieve team goals. Understands stakeholder interests and creates long-term partnerships through relationship-building efforts. | Displays some ability to lead and inspire others. May show empathy and focus on people inconsistently. Moderate ability to maintain and build relationships with key stakeholders. Builds relationships when needed to meet goals. Some awareness of stakeholder interests. Maintains connections, but may not actively deepen them. | Demonstrates limited capability in leading or inspiring others. Social interaction may be minimal or strained. Struggles to build and maintain relationships. Engages with stakeholders minimally. Limited understanding of mutual interests. Rarely invests in building or maintaining long-term relationships. |
| **Thinks Strategically**| Approaches work with a strong focus on the bigger picture. Operates independently with minimal guidance. Demonstrates a commercial and strategic mindset, regularly anticipating trends and their impact. Considers both short- and long-term impact of decisions. Translates departmental strategy into clear, meaningful actions for self and others. | Demonstrates some awareness of the bigger picture but may need occasional guidance. Understands strategy in parts but may not consistently anticipate trends or broader implications. Acknowledges short- and long-term implications, though not always fully. Can link strategy to actions but may need support or clarification. | Focus tends to be on immediate tasks. Requires frequent guidance. Displays limited awareness of trends or the strategic impact of work. Focuses mostly on immediate tasks. Limited awareness of broader implications or difficulty turning strategy into clear actions. |
| **Solves Challenges** | Consistently addresses problems and challenges with confidence and resilience. Takes a diligent, practical, and solution-focused approach. Manages conflicting departmental and people priorities effectively and consistently weighs them when making decisions. | Has the ability to address problems but may need time or support to build confidence and resilience. Attempts a practical approach but not always solution-focused. Manages departmental and people priorities but may not always weigh them evenly when making decisions. | Struggles to address problems confidently. May rely heavily on others. Practical or solution-oriented approaches are limited. Struggles to manage conflicting priorities and rarely weighs them appropriately when making decisions. |
| **Steers Change** | Thrives in change and complexity. Manages new ways of working with adaptability, flexibility, and decisiveness during change. Acts as a role model for positive change, inspiring others and clearly translating the change journey into defined actions. | Demonstrates ability to cope with change and can adapt when needed. May need support to remain flexible or decisive in uncertain situations. Supports change efforts and sometimes inspires others, but may need help translating the journey into clear actions. | Struggles with change or uncertainty. May resist new ways of working and has difficulty adapting or deciding in changing circumstances. Rarely acts as a role model for change and struggles to inspire or define clear actions in the change journey. |

---

**"SHAPE" Level Interpretation Matrix**
| Competency | High (3.5-5.0) | Moderate (2.5-3.49) | Low (1.0-2.49) |
| :--- | :--- | :--- | :--- |
| **Drives Results** | Consistently demonstrates high motivation and initiative to exceed expectations. A strong drive to achieve goals, targets, and results. Seeks fulfillment through impact. High focus on achieving outcomes against set targets and delivers consistent performance to exceed own goals. Shows perseverance and determination to achieve tasks and goals despite challenges. | Demonstrates motivation and takes initiative occasionally. Demonstrates a drive to achieve goals, but may need support. Interest in making an impact is present but not sustained. Moderate focus on outcomes and performance tracking; may occasionally lack focus. Shows perseverance to achieve tasks but may require support in overcoming setbacks or challenges. | Demonstrates limited motivation or initiative; may meet expectations but does not show a consistent drive to exceed them. Fulfillment from work or desire to make an impact is not clearly evident. Low focus on outcomes; may not track performance against goals consistently. There may be a lack of perseverance and problem-solving when faced with setbacks. |
| **Leads People** | Consistently takes time to focus on both personal and professional growth - for both self and others. Actively pursues continuous improvement and excellence; shows clear willingness to learn and unlearn. Strong ability to resolve problems with team members proactively and achieve common goals. Makes contributions on a continual basis, creates trust and teamwork. | Focuses on personal and professional growth and engages in learning activities but may not do so consistently. Moderate openness to learning and unlearning. Cooperates with team members in most situations but may need guidance to work through conflicts. Makes contributions intermittently and may not always address conflicts when they arise. | Rarely focuses on personal or professional growth. Engagement in learning is limited and may resist feedback or change. Seldom works collaboratively with team members. Rarely contributes meaningfully and may avoid resolving conflicts, often leaving issues unaddressed. |
| **Manages Stakeholders**| Consistently shows capability to lead and inspire others. Displays strong empathy, understanding, and a focus on people. Builds relationships with ease and enjoys social interaction. Strong ability to identify and build relationships and connections. Understands stakeholder needs and mutual interests. Works to build long-term relationships. | Displays some ability to lead and inspire others. May show empathy and focus on people but not consistently. Builds relationships but may need support. May have only partial understanding of stakeholder needs and mutual interests. Works to build long-term relationships but may be inconsistent. | Demonstrates limited capability in leading or inspiring others. Social interaction may be minimal or strained. Struggles to build and maintain relationships. Demonstrates limited understanding of stakeholder needs or interdependencies, and does not work to build long-term relationships. |
| **Thinks Strategically**| Approaches work with a strong focus on the bigger picture. Operates independently with minimal guidance. Demonstrates a commercial and strategic mindset, regularly anticipating trends and their impact. Understands potential risks and seeks guidance to address the issues. Strong ability to revise strategies based on team needs while prioritising tasks accordingly in order to meet set deadlines. | Demonstrates awareness of the bigger picture but may need occasional guidance. Understands strategy in parts but may not consistently anticipate trends or broader implications. Can identify risks with some guidance and seeks input occasionally to address issues. Demonstrates some ability to revise plans but may need reminders to prioritise effectively. | Focus tends to be on immediate tasks. Requires frequent guidance. Displays limited awareness of trends or the strategic impact of work. Low ability to align goals with team direction and recognise potential risks. Requires frequent support to address issues and struggles to revise plans independently. |
| **Solves Challenges** | Consistently addresses problems and challenges with confidence and resilience. Takes a diligent, practical, and solution-focused approach to solving issues. Will likely remain composed in the face of setbacks and approach problems with a positive “can do” attitude. | Demonstrates ability to address problems but may need support or time to build confidence and resilience. Attempts a practical approach but not always solution-focused. Moderate ability to identify issues proactively, and takes action when promoted. Sometimes may struggle to remain composed under pressure. | Struggles to address problems confidently. May rely heavily on others and may not take a practical or solution-oriented approach. Does not prioritise working with others to solve problems and identify solutions. Struggles to remain composed under pressure or maintain a positive approach. |
| **Steers Change** | Thrives in change and complexity in the workplace. Manages new ways of working with adaptability, flexibility, and decisiveness during uncertainty. Supports implementation of new change initiatives and takes appropriate follow-up action. | Generally copes with change and can adapt when needed. May need support to remain flexible or decisive in uncertain situations. Operates with a degree of comfort when facts are not fully available and support change initiatives, but follow-up action may be delayed or inconsistent. | Struggles with change or uncertainty. May resist new ways of working and has difficulty adapting or deciding in changing circumstances. May be uncomfortable operating when facts are unclear and is unlikely to support change initiatives. |
"""
                        # --- Dynamically insert candidate data into the prompt ---
                        final_prompt = master_prompt.format(
                            name=candidate_data['name'],
                            gender=candidate_data['gender'],
                            level=candidate_data['level'],
                            **candidate_data, # Unpacks all score columns
                            **{f"s_{k.replace(' ', '_')}": v for k, v in strength_comments.items()},
                            **{f"d_{k.replace(' ', '_')}": v for k, v in dev_comments.items()}
                        )
                        
                        # --- Live API Call ---
                        report_text = call_gemini_api(final_prompt, gemini_api_key)
                        all_summaries.append({'name': candidate_name, 'summary': report_text})
                        
                        # Update progress bar
                        progress_bar.progress((i + 1) / len(candidate_list))

                st.success("All summaries have been generated successfully!")
                
                # --- Create and provide download link for the results ---
                results_df = pd.DataFrame(all_summaries)
                
                output_results = io.BytesIO()
                with pd.ExcelWriter(output_results, engine='xlsxwriter') as writer:
                    results_df.to_excel(writer, index=False, sheet_name='Generated Summaries')
                processed_results = output_results.getvalue()

                st.dataframe(results_df)

                st.download_button(
                    label="⬇️ Download All Summaries (.xlsx)",
                    data=processed_results,
                    file_name="all_candidate_summaries.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"An error occurred while processing the files: {e}")
        st.warning("Please ensure your uploaded files match the format of the downloadable templates.")

else:
    st.info("Please upload both the scores and comments Excel files and provide your API key in the sidebar to begin.")
