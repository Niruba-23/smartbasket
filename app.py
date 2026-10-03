import streamlit as st
import smartbasket as sb

st.set_page_config(page_title="SmartBasket", page_icon="🧺", layout="centered")
st.title("🧺 SmartBasket")
st.caption("Intelligent Shopping Billing and Sales Analytics System")

df = sb.load_data()
tab1, tab2, tab3 = st.tabs(["🧾 Billing", "📊 Dashboard", "💬 Chatbot"])

with tab1:
    if "cart" not in st.session_state:
        st.session_state.cart = []
    customer = st.text_input("Customer name", "Walk-in Customer")
    c1, c2 = st.columns([3, 1])
    product = c1.selectbox("Product", list(sb.PRODUCTS))
    qty = c2.number_input("Qty", 1, 50, 1)
    if st.button("Add item"):
        sb.add_item(st.session_state.cart, product, int(qty))
    discount = st.slider("Discount %", 0, 30, 5)
    if st.session_state.cart:
        bill, totals = sb.calculate_bill(st.session_state.cart, discount)
        st.code(sb.print_invoice(bill, totals, customer, discount))
        if st.button("Clear bill"):
            st.session_state.cart = []
            st.rerun()

with tab2:
    m = sb.summary(df)
    a, b, c = st.columns(3)
    a.metric("Revenue", f"Rs {m['total_revenue']:,}")
    b.metric("Bills", m["bills"])
    c.metric("Items sold", m["items_sold"])
    for kind in ["top", "daily", "category"]:
        st.pyplot(sb.plot_chart(kind, df))

with tab3:
    q = st.text_input("Ask SmartBasket", "top 5 products")
    if q:
        text, kind = sb.chatbot_reply(q, df)
        st.text(text)
        if kind:
            st.pyplot(sb.plot_chart(kind, df))
