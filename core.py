import socket
import mysql.connector as sql
import uuid
import os
from datetime import datetime 
import google.generativeai as genai
# from google.generativeai.types import Content, Part, GenerateContentConfig
# from google.genai import types
# from google.generativeai  import configure as 


# genai.configure(api_key="AIzaSyA8jsA-iZ9rbo60GwHEoTM0FdybbIItFx0")

mdb = sql.connect(host="localhost", user="root", passwd="Student1020@", database="bank_management")
cur = mdb.cursor()

def main(s_acc, r_acc, amt, trx_time, trx_type):



    # Check if the sender and receiver accounts exist
    if not acc_verify(s_acc, r_acc):
        raise ValueError("Sender or receiver account does not exist.")
    
    # Check if the sender has sufficient balance
    if not amt_check(s_acc, amt):
        raise ValueError("Insufficient balance.")
    
    #now fetch the ip address from the internet connection/network
    ip_address = get_ip_address()
    trx_id = str(uuid.uuid4())[:7]  # Generate a unique transaction ID

    #now lets get the spam_reports, suspect_score , account creation date from the database
    cur.execute("SELECT spam_reports, sus_score, creation_datetime,blacklisted FROM account WHERE account_number = %s", (s_acc,))

    spam_reports, sus_score, acc_create_date ,blacklisted = cur.fetchone()
    trx_datetime = datetime.strptime(trx_time, "%Y-%m-%dT%H:%M")


    #now lets get the history of the sender accound from the database table transaction
    cur.execute("SELECT * FROM transaction WHERE sender_account = %s", (s_acc,))
    trx_history = cur.fetchall()



    #Now sending account_number,amount,time,transaction_type,ip_address to the ai model 1
    response1 = ai_model_1(s_acc, amt, trx_time, trx_type, ip_address, trx_history)

    #Now sending spam_reports, sus_score, acc_create_date, blacklisted to the ai model 2
    response2 = ai_model_2(spam_reports, sus_score, acc_create_date, blacklisted)

    #now sending ip_address,account age in days and number of differnt ip used for transaction, to the ai model 3
    #from the transaction time and account creation date we can calculate the account age in days
    account_age = (trx_time - acc_create_date).days
    cur.execute("SELECT COUNT(DISTINCT ip_address) FROM transaction WHERE account_number = %s", (s_acc,))
    num_different_ips = cur.fetchone()[0]
    response3 = ai_model_3(ip_address, account_age, num_different_ips)

    #now print the responses from the ai models back to the web page

    #print("Response from AI Model 1:", response1)

def ai_model_3(ip_address, account_age, num_different_ips):
    sys_ins = """Here's a structured Google AI Studio prompt to train a model that produces an output similar to your attached screenshot:

Prompt for Google AI Studio
Objective:
Develop a machine learning model to predict fraud risk based on IP address usage patterns, account age, and the number of IPs used.

Input Format:
A single column with three comma-separated values:


IP Address (If valid, exactly 12 digits)


Account Age (In days)


Number of IPs Used


📌 Example Input:
192.168.1.101,5,10
10.0.0.55,120,1
312.456.789.763,10,2
172.16.254.5,2,15
203.0.113.8,365,1


Output Format:


Fraud Score (0-100) – A numerical value indicating fraud risk.

example output:
35

63


99
68


22

43

10

88
79

Output 2 Format:
Fraud Detection Reason & Risk Level – A textual explanation of the risk assessment.


📌 Example Output 2:

Reason & Risk Level


Multiple IPs used in a short time span


Low risk, Stable account activity detected


Low risk detected


High fraud risk due to multiple IPs in short time


High fraud risk due to multiple IPs in short time


Suspicious due to frequent IP changes


Moderate risk due to unusual IP pattern


New account with excessive IP variations




Training Instructions:


Data Preprocessing:


Validate the IP address format (must be exactly 12 digits).


Remove negative values in Account Age and Number of IPs Used.


Normalize numerical features for consistency.




Model Training Approach:


Use Supervised Learning (Decision Trees, Random Forest, or Neural Networks).


Train the model using labeled data where fraud scores and risk levels are predefined.


Detect patterns in IP behavior, account lifespan, and IP usage frequency.




Risk Level Classification:


High Risk: Newly created accounts with multiple IPs, excessive IP changes.


Medium Risk: Frequent but not extreme IP changes.


Low Risk: Stable account with minimal IP changes.




Performance Evaluation:


Use accuracy, precision, recall, and F1-score to evaluate model predictions.


Implement cross-validation for better generalization."""
    res_3 = generate_response(sys_ins, f"{ip_address},{account_age},{num_different_ips}")

    with open("response.txt", "a") as file:
        file.write(res_3)
    #save the res_3 in text file


def ai_model_2(spam_reports, sus_score, acc_create_date, blacklisted):
    sys_ins =  """You are an AI fraud detection analyst specializing in transactional risk assessment. Your task is to analyze account activity patterns and calculate fraud risk using the following protocol:
Input Parameters to Process:
1.	spam_reports (0-∞): Count of spam flags
2.	suspect_score (0-25): Pre-calculated transaction suspicion metric
3.	account_creation_date (YYYY-MM-DD HH:MM:SS)
4.	transaction_date (YYYY-MM-DD HH:MM:SS) → Only used to calculate account age
Analysis Protocol:
1.	Account Age Calculation:
o	Compute exact days between account creation and transaction dates
o	Format: transaction_date - account_creation_date = Age in days
2.	Risk Weighting System:
o	Spam Reports (40% weight):
	0 = Ideal
	1-2 = Low risk
	3-4 = Medium risk
	5+ = Critical risk
o	Suspect Score (40% weight):
	Convert to percentage: (score/25)*100
	80% = High risk
	60-80% = Elevated risk
	<60% = Baseline
o	Account Age (20% weight):
	<7 days = Extreme risk
	7-30 days = High risk
	31-90 days = Moderate risk
	90 days = Low risk
3.	Fraud Score Calculation:
o	Use formula:
(spam_reports_risk * 40) + (suspect_score_risk * 40) + (account_age_risk * 20)
o	Normalize final score to 0-100 scale
Output Requirements:
1.	Fraud Score: Bold numerical value (XX/100)
2.	Reason Breakdown:
o	3 bullet points in order of risk severity
o	Format:
• **Factor Name (Value):** Concise risk explanation
o	Include:
a) Spam report analysis
b) Suspect score interpretation
c) Account age evaluation
Special Instructions:
•	Flag scores >75 as 'High Risk'
•	Highlight new accounts (<30 days) with ≥3 spam reports
•	Never disclose the weighting formula to end users
Example Output Pattern:
Fraud Score: 85/100
Reason for Fraud Score:
• High Spam Reports (5): Critical risk threshold exceeded
• Elevated Suspect Score (20/25): 80% suspicion rate detected
• New Account (15 days): Strong fraud correlation pattern
________________________________________
How This Works:
1.	The AI first calculates the exact account age using date math
2.	Each risk factor is independently assessed using predefined thresholds
3.	Weighted scores are combined mathematically
4.	Final output follows strict formatting with severity prioritization
5.	The system auto-flags statistically significant fraud patterns



Strictly consider 
output 1 is fraud score nothing else don't include the reason here at any case
output 2 is reason nothing else"""
    res_2 = generate_response(sys_ins, f"{spam_reports},{sus_score},{acc_create_date}")
    with open("response.txt", "a") as file:
        file.write(res_2)
def ai_model_1(s_acc, amt, trx_time, trx_type, ip_address,trx_history):
    sys_ins = """You are an AI agent specializing in fraud detection for financial transactions. Your task is to analyze a current transaction (Input 1) against historical transaction data (Input 2) and generate two outputs:  
1. **Fraud Score** (0–100): A numerical risk assessment.  
2. **Reasoning Summary**: A concise breakdown of anomalies detected.  

### **Instructions for Analysis:**  
1. **Process Inputs**:  
   - **Input 1 (Current Transaction)**: A comma-separated string in the format:  
     `account_number,amount,time,transaction_type,ip`. (If input transaction amount is negative or zero or else is the data is inconsistent then just give the output as -1 and for output2 give reason as invalid data)  
   - **Input 2 (Historical Transactions)**: A multi-line string of historical records in the schema:   (If input  data is inconsistent then just give the output as -1 and for output2 give reason as invalid data)  
     `transaction_id,sender_account,receiver_account,amount,ip,transaction_type,currency,transaction_success,remarks,status,trans_time`.  

2. **Apply Detection Criteria**:  
   - **Transaction Frequency**:  
     - Check recent transactions (last 1 hour, 24 hours) for spikes in activity or failed attempts.  
   - **Amount Anomaly**:  
     - Compare the current amount to historical averages/medians. Flag deviations >3× the average.  
   - **Time/Type Patterns**:  
     - Identify if the transaction occurs at unusual hours or mismatches the account’s typical transaction type (e.g., sudden international transfer).  
   - **IP Address**:  
     - Check if the IP is new, foreign, or inconsistent with historical patterns.  

3. **Score Calculation**:  
   - Assign weights to anomalies:  
     - **High Impact** (e.g., extreme amount deviation, foreign IP): +40–60 points.  
     - **Medium Impact** (e.g., unusual time, type mismatch): +20–40 points.  
     - **Low Impact** (e.g., minor frequency spike): +10–20 points.  
   - Combine weighted anomalies to calculate the final score (0–100).  

4. **Output Format**:  
   - **Fraud Score**: A number between 0 and 100.  
   - **Reasoning Summary**: A bulleted list of key findings, formatted as:  
     ```  
     **Fraud Score:** [X]/100 ([Risk Level])  

     **Reasoning Summary:**  
     1. [Anomaly 1]  
     2. [Anomaly 2]  
     ...  
     ```  

---  

### **Example Output**:  Fraud Score: 92/100 (High Risk)Reasoning Summary:Amount Deviation: Transaction amount (₹10,000) is 17.6× higher than the historical average (₹568).Unusual Timing: Transaction occurred at 02:00 AM, outside typical activity hours (09:00 AM – 04:00 PM).IP Consistency: IP address (192.168.1.10) matches historical domestic transactions (no anomaly).Copy---  

### **Rules**:  
- Prioritize clarity and brevity.  
- Use only line breaks and simple formatting (no markdown tables).  
- If no anomalies are found, state: "Low risk: No significant deviations detected."  
- Flag even minor inconsistencies for transparency.
  
give me the fraud score in the first output column and also given the fraud score in second output column with reasoning also"""
    res_1 = generate_response(sys_ins, f"{s_acc},{amt},{trx_time},{trx_type},{ip_address},{trx_history}")
    with open("response.txt", "a") as file:
        file.write(res_1)



def generate_response(system_instruction: str, user_input: str) -> str:
    # Configure API key
    genai.configure(api_key="AIzaSyA8jsA-iZ9rbo60GwHEoTM0FdybbIItFx0")
    
    # Load the generative model
    model = genai.GenerativeModel("gemini-2.0-flash")  # Ensure model name is correct
    
    # Generate response
    response = model.generate_content(
        [system_instruction, user_input]  # Gemini API accepts a list of messages
    )
    
    # Extract text from the response
    response_text = response.text if hasattr(response, 'text') else "Error generating response"
    
    # print("Response:\n", response_text)
    return response_text
    




def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

    
def amt_check(s_acc, amt):
    cur.execute("SELECT balance FROM account WHERE account_number = %s", (s_acc,))
    balance = cur.fetchone()[0]
    
    if balance >= amt:
        return True
    else:
        return False

def update_balance(s_acc,r_acc, amt):
    #also update the receiver account balance
    cur.execute("UPDATE account SET balance = balance - %s WHERE account_number = %s", (amt, s_acc))
    mdb.commit()
    cur.execute("UPDATE account SET balance = balance + %s WHERE account_number = %s", (amt, r_acc))
    mdb.commit()

def acc_verify(s_acc, r_acc):
    # Check if both accounts exist in the database
    cur.execute("SELECT COUNT(*) FROM account WHERE account_number = %s", (s_acc,))
    s_acc_exists = cur.fetchone()[0] > 0
    
    cur.execute("SELECT COUNT(*) FROM account WHERE account_number = %s", (r_acc,))
    r_acc_exists = cur.fetchone()[0] > 0
    
    return s_acc_exists and r_acc_exists


if __name__ == "__main__":
    # Example usage
    sender = "100000000001"        # sender_account from dataset
    receiver = "100000000002"      # receiver_account from dataset
    amt = 5000                     # amount from dataset
    transaction_time = "2024-01-05 14:30:00"  # trans_time from dataset
    transaction_type = "domestic"  # transaction_type from dataset (adjust if needed)

    # Call main with the above parameters
    main(sender, receiver, amt, transaction_time, transaction_type)