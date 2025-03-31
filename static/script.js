document.getElementById("transactionForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector("button[type='submit']");
    const loading = document.querySelector(".loading");
    const responseContainer = document.getElementById("responseContainer");

    submitBtn.disabled = true;
    loading.style.display = "block";
    responseContainer.style.display = "none";

    try {
        const formData = {
            sender_account: document.getElementById("senderAccount").value.trim(),
            receiver_account: document.getElementById("receiverAccount").value.trim(),
            amount: parseFloat(document.getElementById("amount").value),
            transaction_type: document.getElementById("transactionType").value,
            transaction_time: document.getElementById("time").value.trim()
        };

        const response = await fetch("/transaction", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || result.message || `Transaction failed (${response.status})`);
        }

        // Wait 15 seconds before showing results
        setTimeout(async () => {
            try {
                const responseFile = await fetch("/get_response");
                const responseData = await responseFile.text();
                
                responseContainer.innerHTML = `<pre>${responseData}</pre>`;
                responseContainer.style.display = "block";
                alert(`Success! Transaction ID: ${result.transaction_id}`);
            } catch (error) {
                console.error("Error fetching response:", error);
                alert("Error loading transaction analysis");
            }
        }, 15000);

        e.target.reset();
        
    } catch (error) {
        console.error("Transaction error:", error);
        alert(`Transaction failed: ${error.message}`);
    } finally {
        submitBtn.disabled = false;
        loading.style.display = "none";
    }
});