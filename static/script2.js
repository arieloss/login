document.addEventListener("DOMContentLoaded", function () {
    const studentForm = document.getElementById("studentForm");
    const studentsTable = document.getElementById("studentsTable");
    const idField = document.getElementById("id");
    console.log("Fichier script2.js chargé avec succès !");


    // Fonction pour afficher/masquer les champs en fonction de la qualité
    function toggleFields() {
        const qualite = document.getElementById("qualite").value;
        const etudiantFields = document.getElementById("etudiantFields");

        etudiantFields.style.display = qualite === "Etudiant" ? "block" : "none";
    }

    // Charger les inscriptions dans la table
    async function loadStudents() {
        try {
            const response = await fetch("http://127.0.0.1:8000/inscriptions");
            const students = await response.json();
    
            studentsTable.innerHTML = ""; // Clear the table
            students.forEach(student => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <a href="/info?id=${student.id}" class="text-primary">${student.id}</a>

                    <td>${student.nom}</td>
                    <td>${student.prenom}</td>
                    <td>${student.qualite}</td>
                    <td>${student.annee}</td>
                    <td>${student.email}</td>
                    <td>${student.numero}</td>
                    <td>${student.matricule}</td>
                    <td>${student.annees_etude}</td>
                `;
                studentsTable.appendChild(row);
            });
        } catch (error) {
            console.error("Erreur de chargement des étudiants:", error);
        }
    }

    // Ajouter un étudiant via le formulaire
    document.querySelector(".btn-primary").addEventListener("click", async function (e) {
        e.preventDefault();

        const studentData = {
            id: idField.value,
            qualite: document.getElementById("qualite").value,
            nom: document.getElementById("nom").value,
            prenom: document.getElementById("prenom").value,
            email: document.getElementById("email").value,
            numero: document.getElementById("numero").value,
            matricule: document.getElementById("matricule").value,
            annee: document.getElementById("annee").value,
            annees_etude: document.getElementById("anneesEtude").value
        };

        try {
            const response = await fetch("http://127.0.0.1:8000/inscription", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(studentData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                alert(`Erreur : ${errorData.detail}`);
                return;
            }

            alert("Inscription ajoutée avec succès!");
            loadStudents();
            // Logs pour vérifier
        console.log("Tentative d'effacement des champs...");
        clearFormFields(studentForm); // Efface les champs manuellement
        console.log("Formulaire effacé !");
        } catch (error) {
            console.error("Erreur de connexion:", error);
            alert("Erreur de connexion à l'API");
        }
    });

    function clearFormFields(form) {
        console.log("Effacement des champs...");
        Array.from(form.elements).forEach(element => {
            if (element.type !== "button" && element.type !== "submit") {
                console.log(`Effacement du champ : ${element.name} (avant : "${element.value}")`);
                element.value = ""; // Efface la valeur
                console.log(`Après effacement : "${element.value}"`);
            }
        });
        console.log("Effacement terminé !");
    }
    
    

    // Récupérer l'ID depuis le backend
    async function fetchLatestId() {
        try {
            const response = await fetch("http://127.0.0.1:8000/latest-id");
            if (response.ok) {
                const data = await response.json();
                if (data.id) {
                    idField.value = data.id; // Mettre à jour le champ ID
                }
            }
        } catch (error) {
            console.error("Erreur lors de la récupération de l'ID:", error);
        }
    }

    

    



    // Appeler fetchLatestId périodiquement
    const intervalId = setInterval(fetchLatestId, 5000);

    // Nettoyer l'intervalle en quittant la page
    window.addEventListener("beforeunload", () => clearInterval(intervalId));

    // Charger les étudiants existants et initialiser les champs
    loadStudents();
    document.getElementById("qualite").addEventListener("change", toggleFields);
});
