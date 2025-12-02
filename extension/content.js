/* AI EMAIL CATEGORIZER - FINAL CLIENT SCRIPT */
const API_URL = "https://email-ai-categorizer-git-main-nihardeeps-projects.vercel.app/categorize";
const APP_ID = 'sdk_EmailCategory_9b980e3e61'; 

console.log("🚀 AI Extension Loading...");

InboxSDK.load(2, APP_ID).then(function(sdk){
    console.log("✅ InboxSDK Loaded!");

    sdk.Lists.registerThreadRowViewHandler(async function(threadRowView){
        
        // Safety Check
        const existingLabels = threadRowView.getLabels();
        const myCategories = ["Job/Recruiter", "IMPORTANT", "READ", "DELETE"];
        if (existingLabels.some(label => myCategories.includes(label.title))) return;

        // Get Data
        const subject = threadRowView.getSubject();
        const snippet = threadRowView.getSnippet(); 
        if (!subject) return;

        try {
            // Send to Backend
            const response = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ subject, snippet })
            });

            const data = await response.json();

            // Apply Label
            if (data.category) {
                console.log(`🏷️ ${data.category}: ${subject}`);
                let labelColor = "gray"; 
                let labelTitle = data.category;

                if (data.category === "JOB") { labelColor = "purple"; labelTitle = "Job/Recruiter"; }
                else if (data.category === "IMPORTANT") labelColor = "red";
                else if (data.category === "READ") labelColor = "blue";
                else if (data.category === "DELETE") labelColor = "black";

                threadRowView.addLabel({
                    title: labelTitle,
                    iconBackgroundColor: labelColor,
                    foregroundColor: "white"
                });
            }
        } catch (err) {
            console.error("❌ API Error:", err);
        }
    });
});
