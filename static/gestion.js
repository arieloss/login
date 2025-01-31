// Gestion des onglets
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
    });
});

// Récupérer les données pour le tableau de bord
async function fetchDashboardData() {
    try {
        const response = await fetch('http://192.168.100.6:8000/api/stats');
        const data = await response.json();
        document.getElementById('disponible-count').textContent = data.disponible || 0;
        document.getElementById('pret-count').textContent = data.en_pret || 0;
        document.getElementById('maintenance-count').textContent = data.en_maintenance || 0;
        document.getElementById('retard-count').textContent = data.retard || 0;
    } catch (error) {
        console.error("Erreur lors du chargement des données du tableau de bord :", error);
    }
}

// Charger la liste des équipements
async function loadStocks() {
    try {
        const response = await fetch('http://192.168.100.6:8000/api/stocks');
        const stocks = await response.json();
        const tableBody = document.getElementById('stocks-table');
        tableBody.innerHTML = '';
        stocks.forEach(stock => {
            const row = `
                <tr>
                    <td>${stock.id}</td>
                    <td>${stock.designation}</td>
                    <td>${stock.caracteristique}</td>
                    <td>${stock.quantite}</td>
                    <td>
                        <button onclick="emprunterEquipement(${stock.id})">Emprunter</button>
                        <button onclick="rendreEquipement(${stock.id})">Rendre</button>
                    </td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    } catch (error) {
        console.error("Erreur lors du chargement des équipements :", error);
    }
}

// Afficher le formulaire d'emprunt
function emprunterEquipement(id) {
    const form = document.getElementById('emprunt-form');
    form.classList.add('active');
    document.getElementById('form-emprunt').onsubmit = function (event) {
        event.preventDefault();
        validerEmprunt(id);
    };
}

// Afficher le formulaire de retour pour un équipement donné
function rendreEquipement(id) {
    const form = document.getElementById('retour-form'); // Formulaire de retour
    form.classList.add('active'); // Afficher le formulaire

    // Lors de la soumission du formulaire, valider le retour
    document.getElementById('form-retour').onsubmit = function (event) {
        event.preventDefault(); // Empêcher le rechargement de la page
        validerRendu(id); // Appeler la fonction pour traiter le retour
    };
}


// Valider l'emprunt
async function validerEmprunt(id) {
    const matricule = document.getElementById('matricule').value.trim();
    const nom = document.getElementById('nom').value.trim();
    const prenom = document.getElementById('prenom').value.trim();
    const quantite = document.getElementById('quantite').value;
    const dateRetour = document.getElementById('date_retour').value;

    if (!matricule && (!nom || !prenom)) {
        alert('Veuillez entrer soit un matricule, soit un nom et un prénom.');
        return;
    }

    const empruntData = {
        stock_id: id,
        user_matricule: matricule || null,
        user_nom: nom || null,
        user_prenom: prenom || null,
        quantite: parseInt(quantite, 10),
        date_retour_prevue: dateRetour
    };

    try {
        const response = await fetch('http://192.168.100.6:8000/api/emprunts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(empruntData)
        });

        if (response.ok) {
            alert('Équipement emprunté avec succès');
            closeForm();
            loadStocks();
            loadEmprunts();
        } else {
            const errorData = await response.json();
            alert(`Erreur : ${errorData.detail}`);
        }
    } catch (error) {
        console.error("Erreur lors de l'emprunt :", error);
        alert("Erreur lors de l'emprunt. Veuillez réessayer.");
    }
}

// Fermer le formulaire
function closeForm() {
    document.getElementById('emprunt-form').classList.remove('active');
}

// Valider le retour d'un équipement
async function validerRendu(id) {
    const quantiteRetour = document.getElementById('quantite_retour').value;
    const matricule = document.getElementById('matricule_retour').value.trim();

    if (!matricule || !quantiteRetour) {
        alert('Veuillez renseigner le matricule et la quantité.');
        return;
    }

    const retourData = {
        stock_id: id,
        matricule: matricule,
        quantite: parseInt(quantiteRetour, 10)
    };

    try {
        const response = await fetch('http://192.168.100.6:8000/api/retours', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(retourData)
        });

        if (response.ok) {
            alert('Retour effectué avec succès');
            closeForm();
            loadStocks();
            loadEmprunts();
        } else {
            const errorData = await response.json();
            alert(`Erreur : ${errorData.detail}`);
        }
    } catch (error) {
        console.error("Erreur lors du retour de l'équipement :", error);
        alert("Erreur lors du retour. Veuillez réessayer.");
    }
}


// Charger l'historique des emprunts

// Charger l'historique des emprunts
async function loadEmprunts() {
    try {
        const response = await fetch('http://192.168.100.6:8000/api/emprunts');
        const emprunts = await response.json();
        const tableBody = document.getElementById('emprunts-table');
        tableBody.innerHTML = ''; // Réinitialiser le contenu du tableau

        emprunts.forEach(emprunt => {
            // Conversion des dates en format lisible
            const dateEmprunt = emprunt.date_emprunt 
                ? new Date(emprunt.date_emprunt).toLocaleDateString() 
                : '';
            const dateRetourPrevue = emprunt.date_retour_prevue 
                ? new Date(emprunt.date_retour_prevue).toLocaleDateString() 
                : '';
            const dateRetourReelle = emprunt.date_retour_reelle 
                ? new Date(emprunt.date_retour_reelle).toLocaleDateString() 
                : '';

            // Ajout d'une ligne au tableau
            const row = `
                <tr>
                    <td>${emprunt.matricule || ''}</td>
                    <td>${emprunt.nom || ''}</td>
                    <td>${emprunt.prenom || ''}</td>
                    <td>${emprunt.equipement || ''}</td>
                    <td>${emprunt.quantite || ''}</td>
                    <td>${dateEmprunt}</td>
                    <td>${dateRetourPrevue}</td>
                    <td>${dateRetourReelle || 'Non retourné'}</td>
                    <td>${emprunt.statut || ''}</td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    } catch (error) {
        console.error("Erreur lors du chargement de l'historique des emprunts :", error);
    }
}





// Initialiser la page
fetchDashboardData();
loadStocks();
loadEmprunts();
