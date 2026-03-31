let token = localStorage.getItem("token")

function carregar(){

    fetch("/dados", {
        headers: { Authorization: "Bearer " + token }
    })
    .then(r=>r.json())
    .then(data=>{

        let enviados = data.length
        let confirmados = data.filter(x => x[4] === "CONFIRMADO").length
        let cancelados = data.filter(x => x[4] === "CANCELADO").length

        document.getElementById("total").innerText = enviados
        document.getElementById("confirmados").innerText = confirmados
        document.getElementById("cancelados").innerText = cancelados

        montarGrafico(confirmados, cancelados)

        let html = "<tr><th>Nome</th><th>Telefone</th><th>Status</th></tr>"

        data.forEach(r=>{
            html += `<tr>
                <td>${r[2]}</td>
                <td>${r[3]}</td>
                <td>${r[4]}</td>
            </tr>`
        })

        document.getElementById("tabela").innerHTML = html
    })
}

function montarGrafico(confirmados, cancelados){
    new Chart(document.getElementById("grafico"), {
        type: "doughnut",
        data: {
            labels: ["Confirmados", "Cancelados"],
            datasets: [{
                data: [confirmados, cancelados]
            }]
        }
    })
}

function enviar(){
    fetch("/enviar", {
        method:"POST",
        headers:{
            "Content-Type":"application/json",
            Authorization:"Bearer "+token
        },
        body: JSON.stringify({
            nome: document.getElementById("nome").value,
            telefone: document.getElementById("telefone").value,
            mensagem: document.getElementById("mensagem").value
        })
    }).then(()=>carregar())
}

carregar()
