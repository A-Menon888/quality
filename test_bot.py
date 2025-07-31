from qa_bot import ask_bot

# Test questions
test_questions = [
    "How can I identify the most frequent quality issues?",
    "What should I do when there's too much variation in my process?",
    "How can I investigate the root cause of a recurring problem?",
    "How do I check if my process is capable of meeting specifications?"
]

print("Testing QA Bot...\n")
for question in test_questions:
    print(f"Q: {question}")
    print(f"A: {ask_bot(question)}\n")
    print("-" * 80 + "\n")
