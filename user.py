from st_supabase_connection import SupabaseConnection, execute_query
import streamlit as st

st_supabase_client = st.connection(
    name="basketboule",
    type=SupabaseConnection,
    ttl=None,
)

auth_operation = st.selectbox('Operation',
                              ["sign_up","sign_in_with_password","sign_in_with_otp"])

if auth_operation == "sign_up":
            
    st.write("## Create user")
    lcol, rcol = st.columns(2)
    email = lcol.text_input(label="Enter your email ID")
    password = rcol.text_input(
        label="Enter your password",
        placeholder="Min 6 characters",
        type="password",
        help="Password is encrypted",
    )

    fname = lcol.text_input(
        label="First name",
        placeholder="Optional",
    )

    attribution = rcol.text_area(
        label="How did you hear about us?",
        placeholder="Optional",
    )

    constructed_auth_query = f"st_supabase_client.auth.{auth_operation}(dict({email=}, {password=}, options=dict(data=dict({fname=},{attribution=}))))"

elif auth_operation == "sign_in_with_password":
    
    st.write("## Sign in")
    lcol, rcol = st.columns(2)
    email = lcol.text_input(label="Enter your email ID")
    password = rcol.text_input(
        label="Enter your password",
        placeholder="Min 6 characters",
        type="password",
        help="Password is encrypted",
    )

    constructed_auth_query = (
        f"st_supabase_client.auth.{auth_operation}(dict({email=}, {password=}))"
    )

elif auth_operation == "sign_in_with_otp":
    st.write("## Create user with OTP")
    st.info("Interactive demo not available for `sign_in_with_otp()` due to technical constraints.")
    if email := st.text_input(label="Enter your email ID"):
        st_supabase_client.auth.sign_in_with_otp(dict(email=email))
    token = st.text_input("Enter OTP", type="password")

if st.button('Execute 🪄',
            key="run_auth_query",
            disabled=not constructed_auth_query):
    try:
        response = eval(constructed_auth_query)

        if auth_operation == "sign_up":
            auth_success_message = f"User created. Welcome {fname or ''} 🚀"
        elif auth_operation in "sign_in_with_password":
            auth_success_message = f"""Logged in. Welcome  🔓""" #{response.dict()["user"]["user_metadata"]["fname"] or ''}
        elif auth_operation == "sign_out":
            auth_success_message = "Signed out 🔒"
        elif auth_operation == "get_user":
            auth_success_message = f"""{response.dict()["user"]["email"]} is logged in"""
        elif auth_operation == "get_session":
            if response:
                auth_success_message = (
                    (f"""{response.dict()["user"]["email"]} is logged in""")
                    if response
                    else None
                )
            else:
                raise Exception("No logged-in user session. Log in or sign up first.")

        if auth_success_message:
            st.success(auth_success_message)

        if response is not None:
            with st.expander("JSON response"):
                st.write(response.dict())

    except Exception as e:
        if auth_operation == "get_user":
            st.error("No logged-in user. Log in or sign up first.", icon="❌")
        else:
            st.error(e, icon="❌")