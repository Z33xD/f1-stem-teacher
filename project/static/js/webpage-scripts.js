const modal = document.getElementById("subtopicModalOverlay");
const modalTitle = document.getElementById("modalTitle");
const subtopicButtons = document.getElementById("subtopicButtons")

const subjectData = {
    "Mathematics": [
        { label: "algebra" }, 
        { label: "statistics" }, 
        { label: "probability" }, 
        { label: "graphs", comingSoon: true  }
    ],
    "Physics": [
        { label: "kinematics" }, 
        { label: "mechanics" }, 
        { label: "energy" }, 
        { label: "Momentum & Inertia", comingSoon: true  }
    ],
    "Computer Sc.": [
        { label: "Databases & Data Modelling", comingSoon: true  }, 
        { label: "Algorithms", comingSoon: true  }, 
        { label: "APIs and Data Integration", comingSoon: true  }
    ],
    "Data Science": [
        { label: "Data Cleaning", comingSoon: true  }, 
        { label: "Data Preprocessing", comingSoon: true  }, 
        { label: "Visualisations", comingSoon: true  }, 
        { label: "Classifications & Clustering", comingSoon: true  }
    ]
};

document.querySelectorAll(".browse-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const card = btn.closest(".card");
        const subject = card.querySelector(".card-title").textContent.trim();

        modalTitle.textContent = `Select a subtopic: (${subject})`;
        subtopicButtons.innerHTML = "";

        subjectData[subject].forEach(topic => {
            const button = document.createElement("button");
            button.className = "button sub-btn";
            
            const label = typeof topic === "string" ? topic : topic.label;
            button.textContent = label;

            if (typeof topic === "object" && topic.comingSoon) {
                button.classList.add("coming-soon");
                button.disabled = true;
                button.title = "Coming Soon!";
            } else {
                button.addEventListener("click", () => {
                    window.location.href = `/chatbot/?subtopic=${encodeURIComponent(label)}`;
                });
            }

            subtopicButtons.appendChild(button);
        });

        modal.style.display = "flex";
    });
});

document.querySelector(".close-popup").addEventListener("click", () => {
    modal.style.display = "none";
});

modal.addEventListener("click", e => {
    if (e.target === modal) {
        modal.style.display = "none";
    }
});