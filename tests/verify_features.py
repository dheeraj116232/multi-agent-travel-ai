import ast
content = open('frontend.py', 'r', encoding='utf-8').read()
features = {
    'logging import': 'import logging' in content,
    'rate limiting': 'check_rate_limit' in content,
    'feedback functions': 'save_feedback_to_db' in content,
    'Home section': 'if st.session_state.active_section == "🏠 Home":' in content,
    'TOP DESTINATIONS sidebar': 'TOP DESTINATIONS' in content,
    'Feedback section': '📝 Feedback' in content,
    'user_feedback table': 'user_feedback' in content
}
for feature, present in features.items():
    status = '✓' if present else '✗'
    print(f'{status} {feature}')

print('\\nSyntax check:', 'PASS' if ast.parse(content) else 'FAIL')