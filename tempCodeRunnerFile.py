import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import json
import time
import os
import google.api_core.exceptions

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="StudyAI Pro", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# --- INITIALIZE SESSION STATE ---
if "study_data" not in st.session_state:
    st.session_state.study_data = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "system_status" not in st.session_state:
    st.session_state.system_status = "awaiting" 
if "chat_history" not in st.session_state:      
    st.session_state.chat_history = []          

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');
    
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    .block-container {
        max-width: 950px !important; 
        padding-top: 2rem !important;
    }
    
    p {
        line-height: 1.8 !important;
        font-size: 1.05rem;
        color: #334155;
    }
    h1, h2, h3, h4 {
        color: #0f172a;
        font-weight: 800 !important; 
        letter-spacing: -0.5px;
    }

    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        padding: 1rem 1.5rem !important;
        border-bottom: 2px solid transparent;
        transition: all 0.2s ease-in-out;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #4f46e5 !important;
        border-bottom: 3px solid #4f46e5 !important;
    }
    
    .summary-box {
        background-color: #ffffff;
        border-left: 5px solid #4f46e5;
        padding: 1.8rem;
        border-radius: 8px;
        box-shadow: 0 4px 10px -2px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
        border: 1px solid #e2e8f0;
    }

    .main-title {
        font-size: 3.2rem;
        background: linear-gradient(90deg, #0f172a, #4f46e5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        text-align: center;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .ai-badge {
        text-align: center;
        font-size: 0.9rem;
        color: #8b5cf6;
        font-weight: 600;
        margin-bottom: 2rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 2rem !important;
        border: none !important;
        box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.39) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        margin-top: 1rem;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# 🔑 API Key (Loads from environment for Cloud Run, or paste here for local testing)
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

# --- UI HEADER ---
st.markdown("<h1 class='main-title'>🎓 StudyAI Pro</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Transform notes, PDFs, or photos of whiteboards into interactive modules.</p>", unsafe_allow_html=True)
st.markdown("<p class='ai-badge'>✨ AI-Powered Personalized Learning System using Gemini</p>", unsafe_allow_html=True)

# --- SIDEBAR & SETTINGS ---
with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    difficulty = st.select_slider(
        "Learning Level", 
        options=["Beginner", "Intermediate", "Advanced"], 
        value="Intermediate"
    )
    
    st.markdown("---")
    st.markdown("### 🗺️ System Status")
    
    status_placeholder = st.empty()
    
    def render_sidebar_status(state):
        if state == "awaiting":
            html = """
            <div style="padding: 10px; background: #f1f5f9; border-radius: 8px; border-left: 4px solid #94a3b8;">
                <b style="color: #475569;">🟡 Awaiting Input</b><br>
                <span style="font-size: 0.85rem; color: #64748b;">Ready for your study materials...</span>
            </div>
            """
        elif state == "building":
            html = """
            <div style="padding: 10px; background: #e0e7ff; border-radius: 8px; border-left: 4px solid #4f46e5;">
                <b style="color: #4338ca;">⏳ AI Building Module...</b><br>
                <span style="font-size: 0.85rem; color: #64748b;">Processing context and generating quiz.</span>
            </div>
            """
        else:
            html = """
            <div style="padding: 10px; background: #dcfce7; border-radius: 8px; border-left: 4px solid #22c55e;">
                <b style="color: #15803d;">✅ Module Ready</b><br>
                <span style="font-size: 0.85rem; color: #64748b;">Interactive test generated!</span>
            </div>
            """
        status_placeholder.markdown(html, unsafe_allow_html=True)

    render_sidebar_status(st.session_state.system_status)
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>", unsafe_allow_html=True)
    st.markdown("Powered by **Gemini API** ✨<br>Built by <b>Lakesh Kumar</b>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- MAIN CONTENT INPUT AREA ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📥 Add Your Study Material")

col1, col2 = st.columns(2)
with col1:
    # 📸 UPGRADE: Now accepts Images!
    uploaded_file = st.file_uploader("Drop PDF or Image (PNG/JPG) here", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file:
        st.success(f"✅ `{uploaded_file.name}` loaded successfully!")

with col2:
    user_input = st.text_area("Or Paste Text directly", height=130, placeholder="Paste your lecture notes, book excerpt, or code here...")

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

analyze_button = st.button("⚡ Build My Study Module", type="primary", use_container_width=True)

# --- LOGIC & TRANSITIONS ---
if analyze_button:
    api_payload = None

    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith('.pdf'):
            api_payload = f"Content:\n{extract_text_from_pdf(uploaded_file)}"
        else:
            # It's an image! Read it with PIL
            api_payload = Image.open(uploaded_file)
    elif user_input:
        api_payload = f"Content:\n{user_input}"

    if api_payload is not None:
        st.session_state.system_status = "building"
        render_sidebar_status("building")
        
        with st.status("🧠 Initializing AI Engine...", expanded=True) as status:
            st.write("📖 Reading document context...")
            time.sleep(0.7) 
            st.write(f"⚙️ Adapting logic to **{difficulty}** level...")
            time.sleep(0.7)
            st.write("⚡ Extracting key terminology...")
            time.sleep(0.5)
            st.write("🎯 Formulating knowledge checks...")
            
            prompt = f"""
            You are an expert AI study tutor. The user wants to study the provided content (text or image) at a {difficulty} difficulty level.
            Extract the core educational value from the input.
            You MUST respond ONLY with a valid JSON object. Do not include markdown formatting.
            
            Use this exact JSON structure:
            {{
                "summary": "A concise summary of the core concepts.",
                "explanation": "A deep dive explanation breaking down complex ideas.",
                "flashcards": [ {{"term": "Term", "definition": "Def"}} ],
                "quiz": [ {{"question": "Q?", "options": ["A", "B", "C", "D"], "answer": "B", "explanation": "Why"}} ],
                "study_plan": [ {{"day": "Day 1: Title", "tasks": ["Task 1", "Task 2"]}} ]
            }}
            """

            try:
                # 📸 Send payload (Text string OR PIL Image object) + Prompt to Gemini
                response = model.generate_content([prompt, api_payload])
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                st.session_state.study_data = json.loads(clean_json)
                st.session_state.quiz_submitted = False 
                st.session_state.chat_history = [] 
                st.session_state.system_status = "ready"
                render_sidebar_status("ready")
                status.update(label="✅ Study Module Built Successfully!", state="complete", expanded=False)
            except Exception as e:
                st.session_state.system_status = "awaiting"
                render_sidebar_status("awaiting")
                status.update(label="❌ Generation failed", state="error")
                st.error(f"Error: {e}")
    else:
        st.warning("⚠️ Please provide some study material first!")

# --- DISPLAY RESULTS ---
if st.session_state.study_data:
    data = st.session_state.study_data
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<br>", unsafe_allow_html=True)
    
    head_col1, head_col2 = st.columns([3, 1], vertical_alignment="bottom")
    with head_col1:
        st.markdown("<h2 style='margin-bottom: 0;'>🎉 Module Ready!</h2>", unsafe_allow_html=True)
    with head_col2:
        export_text = f"SUMMARY\n{data['summary']}\n\nEXPLANATION\n{data['explanation']}"
        st.download_button("💾 Export Notes (.txt)", data=export_text, file_name="StudyAI_Notes.txt", mime="text/plain", use_container_width=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 🗺️ UPGRADE: Added Tab 5 for the Study Plan!
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 Core Concept", "📇 Flashcards", "🎯 Interactive Test", "💬 Chat with AI", "📅 Study Plan"])
    
    with tab1:
        st.markdown("### 📌 Executive Summary")
        st.markdown(f"<div class='summary-box'>{data['summary']}</div>", unsafe_allow_html=True)
        
        st.markdown("### 🧠 Deep Dive")
        st.write(data["explanation"])
        
    with tab2:
        st.markdown("### 🔑 Active Recall Flashcards")
        
        # 🗃️ UPGRADE: CSV Export for Anki/Quizlet
        csv_lines = ["Term,Definition"]
        for fc in data["flashcards"]:
            clean_term = fc["term"].replace('"', '""')
            clean_def = fc["definition"].replace('"', '""')
            csv_lines.append(f'"{clean_term}","{clean_def}"')
        csv_data = "\n".join(csv_lines)
        st.download_button("⬇️ Download for Anki/Quizlet (.csv)", data=csv_data, file_name="StudyAI_Flashcards.csv", mime="text/csv")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        for fc in data["flashcards"]:
            with st.expander(f"❓ **{fc['term']}**"):
                st.success(f"**Definition:** {fc['definition']}")
                
        st.markdown("---")
        if st.button("➕ Generate 3 More Flashcards"):
            with st.spinner("Generating more flashcards..."):
                more_cards_prompt = f"""
                Based on this explanation: {data['explanation']}
                Generate 3 MORE unique flashcards that are different from the current ones.
                You MUST respond ONLY with a valid JSON array. No markdown.
                Format: [ {{"term": "Term", "definition": "Def"}} ]
                """
                try:
                    res = model.generate_content(more_cards_prompt)
                    new_cards = json.loads(res.text.replace("```json", "").replace("```", "").strip())
                    st.session_state.study_data["flashcards"].extend(new_cards)
                    st.rerun() 
                except Exception as e:
                    st.error("Could not generate more flashcards. Try again.")
            
    with tab3:
        st.markdown("### 📝 Knowledge Check")
        
        with st.form("quiz_form"):
            for i, q in enumerate(data["quiz"]):
                st.markdown(f"**{i+1}. {q['question']}**")
                st.radio("Options", q["options"], key=f"q_{i}", index=None, label_visibility="collapsed")
                st.markdown("<br>", unsafe_allow_html=True)
            
            submit_quiz = st.form_submit_button("Check My Answers 🎯")
            
        if submit_quiz:
            st.session_state.quiz_submitted = True
            
        if st.session_state.quiz_submitted:
            score = 0
            st.markdown("### 📊 Your Results")
            for i, q in enumerate(data["quiz"]):
                user_choice = st.session_state.get(f"q_{i}")
                correct_choice = q["answer"]
                
                if user_choice == correct_choice:
                    score += 1
                    st.success(f"**{i+1}. Correct!**")
                else:
                    st.error(f"**{i+1}. Incorrect.** You chose: {user_choice if user_choice else 'Skipped'}")
                    st.warning(f"**Correct Answer:** {correct_choice}")
                    st.info(f"💡 **Why?** {q['explanation']}")
                    
            st.metric(label="Final Score", value=f"{score} / {len(data['quiz'])}")
            if score == len(data['quiz']):
                st.balloons()
                
        st.markdown("---")
        if st.button("➕ Generate 3 More MCQs"):
            with st.spinner("Generating more questions..."):
                more_quiz_prompt = f"""
                Based on this explanation: {data['explanation']}
                Generate 3 MORE unique multiple choice questions different from previous ones.
                You MUST respond ONLY with a valid JSON array. No markdown.
                Format: [ {{"question": "Q?", "options": ["A", "B", "C", "D"], "answer": "B", "explanation": "Why"}} ]
                """
                try:
                    res = model.generate_content(more_quiz_prompt)
                    new_quiz = json.loads(res.text.replace("```json", "").replace("```", "").strip())
                    st.session_state.study_data["quiz"].extend(new_quiz)
                    st.session_state.quiz_submitted = False 
                    st.rerun() 
                except Exception as e:
                    st.error("Could not generate more questions. Try again.")
                
    with tab4:
        st.markdown("### 💬 Your Personal AI Tutor")
        st.caption("Didn't understand a concept? Want a real-world example? Ask away!")
        st.markdown("<br>", unsafe_allow_html=True)

        chat_container = st.container(height=450)

        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt := st.chat_input("Ask a question about your notes..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        
                        recent_history = ""
                        for msg in st.session_state.chat_history[-8:-1]: 
                            role = "Student" if msg["role"] == "user" else "Tutor"
                            recent_history += f"{role}: {msg['content']}\n\n"

                        chat_context = f"""
                        You are a helpful tutor. Answer the student's question based primarily on this study material: 
                        {data['explanation']}

                        Here is the recent conversation history for context:
                        {recent_history}

                        Student's new question: {prompt}
                        """
                        
                        try:
                            chat_response = model.generate_content(chat_context)
                            st.markdown(chat_response.text)
                            st.session_state.chat_history.append({"role": "assistant", "content": chat_response.text})
                        except Exception as e:
                            st.error("Oops! API limit reached. Try again in a minute.")
                            
    # 🗺️ UPGRADE: The Structured Study Plan Tab
    with tab5:
        st.markdown("### 📅 Your 3-Day Study Roadmap")
        st.info("Don't cram! Follow this AI-generated plan to master the material step-by-step.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if "study_plan" in data:
            for day in data["study_plan"]:
                st.markdown(f"#### {day['day']}")
                for task in day['tasks']:
                    st.markdown(f"- 🗓️ {task}")
                st.divider()
        else:
            st.warning("No study plan generated for this module.")