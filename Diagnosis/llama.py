import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("LLAMA_API_KEY")
)

simulationPath = r"../path/to/resultSimulation.txt"
violationPath = r"../path/to/violations.txt"
diagnosisPath = r"../path/to/diagnosis.txt"
diagramPath = r"../path/to/diagram.bpmn"

with open(simulationPath, "r") as f:
    simulationContent = f.read()

with open(violationPath, "r") as f:
    violationContent = f.read()

with open(diagramPath, "r") as f:
    diagramContent = f.read()

prompt = f"""
**System/Background Instruction (not to be shown in final answer):**  
You have detailed logs and BPMN data describing a workflow with multiple lanes and user roles. Certain "Violation Instances" indicate conflicts (BoD, SoD, UoC). Your task is to recommend how to modify the number of user resources in each lane or participant group so these violations no longer occur. If no change is needed, specify "maintain."

---

### **Task**  
Analyze the following sections:
1. **Violation Instances**  
2. **Simulation Log**  
3. **Optional BPMN File or Details**

Identify specific lanes, roles, or participant groups that need adjustment to prevent each violation. Propose increases or decreases in user resources as needed. If no change is required, state that explicitly. Provide only the final recommendations in this exact format:

```
Increase "Lane/Participant Name" (Lane/Participant ID) from X to Y.
Reduce "Lane/Participant Name" (Lane/Participant ID) from X to Y.
Maintain "Lane/Participant Name" (Lane/Participant ID) at X.
```

*(Where "Lane/Participant Name" is the name from the BPMN or "Unnamed" if none is provided, and "Lane/Participant ID" is the ID in parentheses.)*

---

### **Violation Instances**  
```
{violationContent}
```

---

### **Simulation Log**  
(Full XML log content follows; each event includes user details, lane, participant, timestamps, userTask, etc. This data shows how tasks were executed, by whom, and in which order.)

```
{simulationContent}
```

---

### **BPMN File**  
(Full BPMN XML content, including lane/role declarations, user assignments, and security attributes.)

```
{diagramContent}
```

---

### **Analysis Instructions**  
- Focus on how many users (resources) are assigned in each lane, role, or participant.  
- Decide whether to increase or decrease those resources to prevent repeated SoD, BoD, or UoC violations.  
- Use the lane or participant name (if available) or "Unnamed" otherwise, along with the BPMN element's ID in parentheses.  
- Provide exact numeric changes if possible (e.g., from 3 to 4).  
- Return only the final statements about increasing, reducing, or maintaining resource counts-no extra commentary.

---

### **Example Format**  
```
Increase "Lane name 1" (Lane_139d80b) from 3 to 4.
Reduce "Lane name 2" (Lane_0zlk836) from 5 to 3.
Maintain "Unnamed" (Participant_11ovzyb) at 2.
```

*(Adjust the lane/user counts as your analysis requires.)*

---

**Final Output**  
Return only the lines indicating your recommended resource adjustments or maintenance, in the style demonstrated above. No other explanation is needed.
"""

messages = [
    {"role": "system", "content": "You are an expert in bpmn modeling and simulation."},
    {"role": "user", "content": prompt},
]

completion = client.chat.completions.create(
    model="meta/llama-3.1-405b-instruct",
    messages=[
        {"role": "system", "content": "You are an expert in bpmn modeling and simulation"},
        {"role": "user", "content": prompt},
    ],
    temperature=0.2,
    top_p=0.7,
    max_tokens=8192,
    stream=True
)

answer = ""

with open(diagnosisPath, "w") as f:
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            partial_text = chunk.choices[0].delta.content
            answer += partial_text
            f.write(partial_text)

messages.append({"role": "assistant", "content": answer})

follow_up_question = (
    """- Binding of duty (BoD) represents a constraint which indicates that certain activities in the process must be performed by the same user or role. BoD can be relevant to the GDPR as, in certain cases, it may be necessary for the same person or role to perform related tasks to ensure data consistency and accuracy. For example, if a person initiates a data update process, it may be necessary for that same person to complete the process to avoid inconsistencies. In this case, it relates to the principle of accuracy and also to data minimization, as it avoids the need to transfer information between multiple users, which could lead to errors. We can find an example of Explaining the Compliance of Security Policies for GDPR in Business Processes 5 this rule in Figure 2.a. If Alice performs task A and Bob performs task B, the rule will be violated.

- Separation of duty (SoD) represents a constraint that requires two or more different roles/users to complete a task. SoD is crucial for data integrity and confidentiality. By requiring different people or roles to perform critical tasks, the risk of fraud, abuse, or unauthorized access to personal data is reduced. This aligns with the GDPR principle of integrity and confidentiality. By preventing a single person from having full control over the data, the risk of manipulation or improper disclosure is minimized. It is also related to the principle of proactive accountability, as it implements controls to demonstrate that measures are taken to protect information. We can find an example of this rule in Figure 2.b. If Alice performs both tasks A and B, the rule will be violated.

- Usage of control (UoC) expresses the maximal number of accesses to a resource (cardinality) or the obligation to delete local copies of a data item after accessing and using these data. It is directly relevant to the GDPR as it focuses on controlling the use and processing of personal data. By establishing conditions on how data can be accessed and used, UoC helps ensure compliance with the principles of purpose limitation, data minimization, integrity, and confidentiality. For example, by limiting the number of accesses to a personal data file, the risk of misuse or unauthorized access is reduced. Additionally, the obligation to delete local copies is directly related to the principle of storage limitation. We can find an example of this rule in Figure 2.c. If Alice performs task B “n+1” times, while the limit imposed by the security policy is n, the rule will be violated.

Correct compliance with GDPR will require great effort, on the one hand, significant adaptation of business processes and, on the other hand, the definition and implementation of organisational and technical measures. Consequently, data controllers must identify and implement appropriate technical and organisational measures according to Article 32 of GDPR, to ensure a level of security corresponding to the identified risks. 

If security policies, I would like to know which GDPR principles and articles are violated taking into account those texts.""")

messages.append({"role": "user", "content": follow_up_question})

new_completion = client.chat.completions.create(
    model="meta/llama-3.1-405b-instruct",
    messages=messages,
    temperature=0.2,
    top_p=0.7,
    max_tokens=8192
)

follow_up_answer = new_completion.choices[0].message.content

with open(diagnosisPath, "a") as f:
    f.write("\n\n" + follow_up_answer)
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            partial_text = chunk.choices[0].delta.content
            answer += partial_text
            f.write(partial_text)