import os
import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# مفتاح Gemini API المدمج
API_KEY = "AQ.Ab8RN6J58G46pYqJ5AowcHhsSOputo9izMg6oALzusOc8WBA5g"

st.set_page_config(page_title="مساعد مواد الكلية", layout="wide")

# قائمة المواد الستة المطابقة للمجلدات
SUBJECTS = ["CS", "DS", "MATH0", "LINEAR", "PROBABILITY", "PROGRAMMING"]

with st.sidebar:
    st.header("📚 اختيار المادة")
    selected_subject = st.selectbox("حدد المادة:", SUBJECTS)
    st.divider()

# قراءة الملفات من مجلد المادة المحددة
@st.cache_resource
def load_subject_materials(subject_name):
    combined_text = ""
    pdf_files = []
    
    if os.path.exists(subject_name) and os.path.isdir(subject_name):
        pdf_files = [f for f in os.listdir(subject_name) if f.lower().endswith(".pdf")]
        for pdf in pdf_files:
            file_path = os.path.join(subject_name, pdf)
            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        combined_text += text + "\n"
            except Exception:
                continue
    return combined_text, pdf_files

subject_context, loaded_pdfs = load_subject_materials(selected_subject)

with st.sidebar:
    st.subheader(f"📂 ملفات مادة {selected_subject}:")
    if loaded_pdfs:
        for p in loaded_pdfs:
            st.markdown(f"- 📄 `{p}`")
    else:
        st.info("لم يتم رفع ملفات PDF لهذه المادة بعد.")

st.title(f"📖 المساعد الذكي لمادة: {selected_subject}")
st.write(f"اسأل في أي جزئية تخص **{selected_subject}** وهيجاوبك ويشرحلك منها مباشرة!")

# مسح المحادثة السابقة عند تغيير المادة
if "active_subject" not in st.session_state:
    st.session_state.active_subject = selected_subject

if st.session_state.active_subject != selected_subject:
    st.session_state.active_subject = selected_subject
    st.session_state.messages = []

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input(f"اكتب سؤالك في {selected_subject}...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not subject_context.strip():
        warning_msg = f"لم يتم العثور على ملفات PDF داخل مجلد {selected_subject}. يرجى رفع ملفات المادة داخل المجلد في GitHub."
        st.warning(warning_msg)
        st.session_state.messages.append({"role": "assistant", "content": warning_msg})
    else:
        try:
            genai.configure(api_key=API_KEY.strip())
            
            try:
                model = genai.GenerativeModel("models/gemini-1.5-flash")
            except Exception:
                model = genai.GenerativeModel("gemini-pro")

            with st.spinner(f"جاري تحضير الشرح من واقع ملفات {selected_subject}..."):
                system_instruction = f"""
                أنت معيد ومساعد دراسي جامعي متخصص في مادة: {selected_subject}.
                المهمة: اعتمد حصرياً وبدقة على المحتوى التالي المستخرج من محاضرات وملخصات {selected_subject}.
                اشرح بأسلوب مبسط ومنظم للطلاب، وحل الأسئلة والمسائل وفق ما ورد في هذه الملفات فقط باللغة العربية.

                المحتوى المعتمد للمادة:
                {subject_context}
                """
                
                full_prompt = f"{system_instruction}\n\nسؤال الطالب: {prompt}"
                response = model.generate_content(full_prompt)
                
                answer = response.text
                with st.chat_message("assistant"):
                    st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

        except Exception as e:
            st.error(f"حدث خطأ: {e}")
