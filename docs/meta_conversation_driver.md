# Conversation based on Simple Meta
You can make use of `frappe_telegram.utils.conversation.collect_conversation_details` to collect the details from a conversation easily.

Conversation handlers for `login` & `signup` makes use of this utility function. Sample below:
```py
    def collect_signup_details(update: Update, context: CallbackContext):
        details = collect_conversation_details(
            key="signup_details",
            meta=[
                dict(label="First Name", key="first_name", type="str"),
                dict(label="Last Name", key="last_name", type="str"),
                dict(key="email", label="Email", type="regex", options=r"^.+\@.+\..+$"),
                dict(key="pwd", label="Password", type="password"),
                # dict(key="gender", label="Gender", type="select", options="Male\nFemale"),
            ],
            update=update,
            context=context,
        )
        if not details.get("_is_complete"):
            raise DispatcherHandlerStop(state=ENTERING_SIGNUP_DETAILS)

        user = frappe.get_doc(dict(
            doctype="User",
            email=details.email,
            first_name=details.first_name,
            last_name=details.last_name,
            enabled=1,
            new_password=details.pwd,
            send_welcome_email=0,
        )).insert(ignore_permissions=True)

        context.telegram_user.db_set("user", user.name)
        update.effective_chat.send_message(
            frappe._("You have successfully signed up as: {0}").format(
                user.name))

        return ConversationHandler.END
```