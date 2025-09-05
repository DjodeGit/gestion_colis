// ================= NAVIGATION =================
function showSection(sectionId) {
  document.querySelectorAll("main section").forEach(sec => sec.classList.add("hidden"));
  document.getElementById(sectionId).classList.remove("hidden");
}

// Afficher accueil par défaut
showSection("home");

// ================= INSCRIPTION =================
document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    nom: document.getElementById("regNom").value,
    email: document.getElementById("regEmail").value,
    password: document.getElementById("regPassword").value
  };

  let res = await fetch("http://127.0.0.1:8000/api/utilisateurs/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  document.getElementById("registerMessage").innerText = res.ok ? "✅ Inscription réussie !" : "❌ Erreur inscription";
});

// ================= CONNEXION =================
document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    email: document.getElementById("logEmail").value,
    password: document.getElementById("logPassword").value
  };

  let res = await fetch("http://127.0.0.1:8000/api/login/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (res.ok) {
    let result = await res.json();
    localStorage.setItem("token", result.token);
    document.getElementById("loginMessage").innerText = "✅ Connexion réussie";
  } else {
    document.getElementById("loginMessage").innerText = "❌ Erreur connexion";
  }
});

// ================= GESTION DES COLIS =================
document.getElementById("colisForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    nom: document.getElementById("colisNom").value,
    description: document.getElementById("colisDescription").value
  };

  let res = await fetch("http://127.0.0.1:8000/api/colis/", {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Authorization": `Token ${localStorage.getItem("token")}`
    },
    body: JSON.stringify(data)
  });

  if (res.ok) {
    document.getElementById("colisForm").reset();
    loadColis();
  } else {
    alert("❌ Erreur ajout colis");
  }
});

// Charger colis
async function loadColis() {
  let res = await fetch("http://127.0.0.1:8000/api/colis/", {
    headers: { "Authorization": `Token ${localStorage.getItem("token")}` }
  });
  let data = await res.json();
  let list = document.getElementById("colisList");
  list.innerHTML = "";
  data.forEach(c => {
    let li = document.createElement("li");
    li.className = "p-2 border rounded";
    li.innerText = `${c.nom} - ${c.description}`;
    list.appendChild(li);
  });
}

// ================= DEMANDE D’ENVOI =================
document.getElementById("demandeForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    destinataire: document.getElementById("destinataire").value,
    adresse: document.getElementById("adresse").value,
    message: document.getElementById("message").value
  };

  let res = await fetch("http://127.0.0.1:8000/api/demandes/", {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Authorization": `Token ${localStorage.getItem("token")}`
    },
    body: JSON.stringify(data)
  });

  document.getElementById("demandeMessage").innerText = res.ok ? "✅ Demande envoyée" : "❌ Erreur envoi";
});

// ================= NOTIFICATIONS =================
async function loadNotifications() {
  let res = await fetch("http://127.0.0.1:8000/api/notifications/", {
    headers: { "Authorization": `Token ${localStorage.getItem("token")}` }
  });
  let data = await res.json();
  let list = document.getElementById("notificationsList");
  list.innerHTML = "";
  data.forEach(n => {
    let li = document.createElement("li");
    li.className = "p-2 border rounded bg-yellow-100";
    li.innerText = `${n.message} - ${n.date}`;
    list.appendChild(li);
  });
}

// ================= AGENTS =================
async function loadAgents() {
  let res = await fetch("http://127.0.0.1:8000/api/agents/", {
    headers: { "Authorization": `Token ${localStorage.getItem("token")}` }
  });
  let data = await res.json();
  let list = document.getElementById("agentsList");
  list.innerHTML = "";
  data.forEach(a => {
    let li = document.createElement("li");
    li.className = "p-2 border rounded";
    li.innerText = `${a.nom} - ${a.email}`;
    list.appendChild(li);
  });
}

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("colisForm");
    const resultat = document.getElementById("resultat");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        // Récupération des valeurs
        const expediteur = {
            nom: document.getElementById("exp_nom").value,
            email: document.getElementById("exp_email").value,
            telephone: document.getElementById("exp_tel").value
        };

        const destinataire = {
            nom: document.getElementById("dest_nom").value,
            email: document.getElementById("dest_email").value,
            telephone: document.getElementById("dest_tel").value,
            adresse: document.getElementById("dest_adresse").value
        };

        try {
            // 1. Enregistrer l'expéditeur
            let resExp = await fetch("/api/expediteurs/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(expediteur)
            });
            let dataExp = await resExp.json();

            // 2. Enregistrer le destinataire
            let resDest = await fetch("/api/destinataires/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(destinataire)
            });
            let dataDest = await resDest.json();

            resultat.textContent = "Expéditeur et Destinataire enregistrés avec succès ✅";
        } catch (error) {
            resultat.textContent = "Erreur lors de l'enregistrement ❌";
        }
    });
});

// Fonction pour afficher une section et cacher les autres
function showSection(sectionId) {
  // Cacher toutes les sections
  document.querySelectorAll("main section").forEach(sec => {
    sec.classList.add("hidden");
  });

  // Afficher la section cliquée
  const target = document.getElementById(sectionId);
  if (target) {
    target.classList.remove("hidden");
  }
}

// ====================== FORMULAIRES ======================

// Inscription
document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    nom: document.getElementById("regNom").value,
    email: document.getElementById("regEmail").value,
    password: document.getElementById("regPassword").value
  };

  try {
    const res = await fetch("/api/register/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const result = await res.json();
    document.getElementById("registerMessage").innerText = result.message || "Inscription réussie ✅";
  } catch (err) {
    document.getElementById("registerMessage").innerText = "Erreur d’inscription ❌";
  }
});

// Connexion
document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    email: document.getElementById("logEmail").value,
    password: document.getElementById("logPassword").value
  };

  try {
    const res = await fetch("/api/login/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const result = await res.json();
    document.getElementById("loginMessage").innerText = result.message || "Connexion réussie ✅";
  } catch (err) {
    document.getElementById("loginMessage").innerText = "Erreur de connexion ❌";
  }
});

// Ajouter un colis
document.getElementById("colisForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    nom: document.getElementById("colisNom").value,
    description: document.getElementById("colisDescription").value
  };

  try {
    const res = await fetch("/api/colis/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const result = await res.json();
    const li = document.createElement("li");
    li.textContent = `${result.nom} - ${result.description}`;
    document.getElementById("colisList").appendChild(li);
  } catch (err) {
    alert("Erreur ajout colis ❌");
  }
});


document.getElementById('contact-form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Empêche le rechargement de la page

    const form = event.target;
    const formData = new FormData(form);
    const data = {
        name: formData.get('name'),
        email: formData.get('email'),
        subject: formData.get('subject'),
        message: formData.get('message')
    };

    try {
        const response = await fetch('http://localhost:3000/send-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        const messageDiv = document.getElementById('form-message');
        if (response.ok) {
            messageDiv.innerHTML = '<p class="text-green-600">Message envoyé avec succès !</p>';
            form.reset(); // Réinitialise le formulaire
        } else {
            messageDiv.innerHTML = '<p class="text-red-600">Erreur lors de l\'envoi du message : ' + result.error + '</p>';
        }
    } catch (error) {
        document.getElementById('form-message').innerHTML = '<p class="text-red-600">Erreur : ' + error.message + '</p>';
    }
});
