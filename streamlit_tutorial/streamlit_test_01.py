import streamlit as st
st.write("Hello Guillermo y Estela")
st.write("This is the second line")
response = st.text_input("Favourite Color?")
print("response: ", response)
st.write(f"Your answer is {response}!!")

is_clicked = st.button("Click Me")
print("is_clicked", is_clicked)

st.write("# This is a H1 Title")
st.write("## This is a H2 Title")
st.write("``` Bash:" \
"This is a code block" \
"```")
st.write("---") # separator
st.write("`This is a code line`")
st.write("This is __negrita__ and this is _italic_ text")

