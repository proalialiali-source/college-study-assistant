import os
import streamlit as st
from google import genai
from pypdf import PdfReader

# مفتاح الـ API المدمج
API_KEY = "AQ.Ab8RN6L0dcsYSC03V54t8mfX1pwThvVT-taScxNHuifgCGHt_Q"

st.set_page_config(page_title="مساعد مواد الكلية", layout="wide")

# قائمة المواد الستة
SUBJECTS = ["CS", "DS", "MATH0", "LINEAR", "PROBABILITY", "PROGRAMMING"]

with st.sidebar:
    st.header("📚 اختيار المادة")
    selected_subject = st.selectbox("حدد المادة:", SUBJECTS)
    st.divider()

# استخراج النصوص من ملفات الـ PDF
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
                        combined_text += f"\n--- ملف: {pdf} ---\n" + text
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
        st.info("لم يتم العثور على ملفات PDF. تأكد من رفعها داخل مجلد المادة.")

st.title(f"📖 المساعد الذكي لمادة: {selected_subject}")
st.write(f"المساعد جاهز للشرح وحل التدريبات بناءً على ملفات ومحاضرات **{selected_subject}** المرفوعة.")

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
        warning_msg = f"لم يتم العثور على ملفات PDF داخل مجلد {selected_subject}."
        st.warning(warning_msg)
        st.session_state.messages.append({"role": "assistant", "content": warning_msg})
    else:
        try:
            client = genai.Client(api_key=API_KEY.strip())

            with st.spinner(f"جاري تحضير الشرح من واقع ملفات {selected_subject}..."):
                system_instruction = f"""
                أنت معيد جامعي متميز ومساعد دراسي متخصص في مادة: {selected_subject}.
                المهمة: اشرح المفاهيم وحل المسائل بالاعتماد الحصري والمباشر على المحتوى التالي المستخرج من محاضرات وملخصات {selected_subject}.
                قدم الشرح باللغة العربية بأسلوب منظم، مبسط وواضح جداً للطلاب.

                المحتوى التعليمي المرفوع:
                {subject_context}
                """

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[system_instruction, f"سؤال الطالب: {prompt}"]
                )

                answer = response.text
                with st.chat_message("assistant"):
                    st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

        except Exception as e:
            st.error(f"حدث خطأ: {e}")
