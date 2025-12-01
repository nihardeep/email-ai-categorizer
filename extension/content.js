/* AI EMAIL CATEGORIZER - CLIENT SCRIPT 
   Connects Gmail -> InboxSDK -> Vercel -> Gemini
*/

// --- CONFIGURATION (UPDATE THESE!) ---
// 1. Your Vercel Backend URL
const API_URL = "https://email-ai-categorizer-git-main-nihardeeps-projects.vercel.app/categorize/"
// 2. Your InboxSDK App ID (from inboxsdk.com)
const APP_ID = 'sdk_EmailCategory_9b980e3e61'; 

console.log("🚀 AI Extension Loading...");

InboxSDK.load(2, APP_ID).then(function(sdk){

    console.log("✅ InboxSDK Loaded!");

    // Runs for every email row visible on screen
    sdk.Lists.registerThreadRowViewHandler(async function(threadRowView){

        // 1. Get Email Data
        const subject = threadRowView.getSubject();
        const snippet = threadRowView.getSnippet(); 

        if (!subject) return;

        // 2. Prepare Payload
        const payload = {
            subject: subject,
            snippet: snippet
        };

        try {
            // 3. Send to Backend
            const response = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            // 4. Handle Visuals based on Category
            if (data.category) {
                
                console.log(`🏷️ ${data.category}: ${subject}`);

                let labelColor = "gray"; 
                let labelTitle = data.category;

                // --- COLOR LOGIC ---
                if (data.category === "JOB") {
                    labelColor = "purple"; // Job Folder
                    labelTitle = "Job/Recruiter";
                }
                else if (data.category === "IMPORTANT") {
                    labelColor = "red";    // Urgent / OTPs
                }
                else if (data.category === "READ") {
                    labelColor = "blue";   // Transaction / Info
                }
                else if (data.category === "DELETE") {
                    labelColor = "black";  // Spam / Promo
                }

                // 5. Apply the Tag to the Row
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
