import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

st.set_page_config(page_title="مساعد الكلية الذكي", layout="wide")

st.title("📚 مساعد مذاكرة مواد الكلية")
st.write("ارفع ملفات الشرح (PDF) واسأل في المنهج وهيجاوبك ويشرحلك منها مباشرة!")

# إعداد القائمة الجانبية لإدخال المفتاح والملفات
with st.sidebar:
    st.header("⚙️ الإعدادات والملفات")
    api_key = st.text_input("أدخل مفتاح Gemini API:", type="password")
    uploaded_files = st.file_uploader("ارفع محاضرات ومذكرات المنهج (PDF)", type=["pdf"], accept_multiple_files=True)

# استخراج النصوص من ملفات الـ PDF
def extract_text_from_pdfs(files):
    full_text = ""
    for file in files:
        reader = PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    return full_text

# إدارة سجل المحادثة
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض الرسائل السابقة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# استقبال سؤال المستخدم
prompt = st.chat_input("اكتب سؤالك هنا بخصوص المنهج...")

if prompt:
    if not api_key:
        st.error("يرجى إدخال مفتاح Gemini API في القائمة الجانبية أولاً.")
    elif not uploaded_files:
        st.warning("يرجى رفع ملف PDF واحد على الأقل للمذاكرة منه.")
    else:
        # عرض سؤال المستخدم
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # تجهيز النموذج واستخراج محتوى الملفات
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        with st.spinner("جاري استخراج الإجابة والشرح من الملفات..."):
            context = extract_text_from_pdfs(uploaded_files)
            
            system_instruction = f"""
            أنت مساعد دراسي جامعي ذكي ومتخصص.
            المهمة: اعتمد فقط على المحتوى التالي المستخرج من محاضرات الكلية لشرح المفاهيم والإجابة عن أسئلة الطالب وحل التدريبات بطريقة مبسطة، منظمة وواضحة جداً باللغة العربية.
            
            المحتوى التعليمي من الملفات:
            {context}
            """
            
            full_prompt = f"{system_instruction}\n\nسؤال الطالب: {prompt}"
            response = model.generate_content(full_prompt)
            
            # عرض رد الذكاء الاصطناعي
            answer = response.text
            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
