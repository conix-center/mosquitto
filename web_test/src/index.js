document.addEventListener('DOMContentLoaded', function() {
    var cy = window.cy = cytoscape({
        container: document.getElementById('cy'),
        boxSelectionEnabled: false,

        style: [{
            selector: 'node',
            css: {
                'content': 'data(label)',
                'text-valign': 'center',
                'text-halign': 'center'
            }
        }, {
            selector: 'node[class="client"]',
            style: {
                "font-size": 6,
                'shape': 'round-rectangle',
                'background-color': 'LightGray'
            }
        }, {
            selector: 'node[class="topic"]',
            style: {
                "font-size": 6,
                'shape': 'ellipse',
                'background-color': 'LightBlue'
            }
        }, {
            selector: 'node[class="client ip"]',
            style: {
                "font-size": 6,
                'shape': 'barrel',
                'background-color': 'Coral'
            }
        }, {
            selector: ':parent',
            css: {
                'text-valign': 'top',
                'text-halign': 'center',
            }
        }, {
            selector: 'edge',
            css: { },
            style: {
                'label': 'data(label)',
                "font-size": 3,
                'width': 1,
                'arrow-scale': 0.5,
                'curve-style': 'bezier',
                'text-rotation': 'autorotate',
                'target-arrow-shape': 'triangle-cross'
            }
        }]
    });

    const client_main = new Paho.MQTT.Client("ws://127.0.0.1:9001/", "client_js_" + new Date().getTime());

    const topic = "$SYS/graph";

    let action = null;

    let oldJSON = null;

    let modal = document.getElementById("modalView");
    let span = document.getElementsByClassName("close")[0];

    let ipElem = document.getElementById("ipDiv");
    let clientElem = document.getElementById("clientDiv");
    let topicElem = document.getElementById("topicDiv");
    let intervalElem = document.getElementById("intervalDiv");

    let msg = document.getElementById("msg");

    client_main.onConnectionLost = onConnectionLost;
    client_main.onMessageArrived = onMessageArrived;

    client_main.connect({ onSuccess: onConnect });

    function onConnect() {
        console.log("Connected!");
        client_main.subscribe(topic);
    }

    function onConnectionLost(responseObject) {
        if (responseObject.errorCode !== 0) {
            console.log("onConnectionLost:" + responseObject.errorMessage);
        }
        client_main.connect({ onSuccess: onConnect });
    }

    function publish(client, dest, msg) {
        console.log('desint :', dest, 'msggg', msg)
        let message = new Paho.MQTT.Message(msg);
        message.destinationName = dest;
        client.send(message);
    }

    function runLayout() {
        cy.layout({
            name: 'cose-bilkent',
            padding: 200,
            animate: true,
            animationDuration: 100,
            animationEasing: 'ease-out'
        }).run();
    }

    function onMessageArrived(message) {
        var newJSON = JSON.parse(message.payloadString);
        msg.value = JSON.stringify(newJSON, undefined, 4);
        console.log(msg.value)

        try {
            cy.json({ elements: newJSON });
            if (!_.isEqual(oldJSON, newJSON)) {
                runLayout();
            }
        }
        catch (err) {
            console.log(err.message)
        }

        oldJSON = newJSON;
    }

    function undisplayModal() {
        modal.style.display = "none";
        ipElem.style.display = "block";
        clientElem.style.display = "block";
        topicElem.style.display = "block";
        intervalElem.style.display = "block";
    }

    function displayModal(action) {
        modal.style.display = "block";
        document.getElementById("title").innerText = action;
        switch (action) {
            case "Connect":
                topicElem.style.display = "none";
                intervalElem.style.display = "none";
                break;
            case "Subscribe":
                intervalElem.style.display = "none";
                break;
            case "Unsubscribe":
                intervalElem.style.display = "none";
                break;
            case "Disconnect":
                topicElem.style.display = "none";
                intervalElem.style.display = "none";
                break;
            case "Publish":
            default:
                break;
        }
    }

    window.onclick = function() {
        if (event.target == modal) {
            undisplayModal()
        }
    }

    span.onclick = function() {
        undisplayModal()
    }

    document.getElementById("connect").addEventListener("click", function() {
        action = "Connect";
        displayModal(action);
    });

    document.getElementById("pub").addEventListener("click", function() {
        action = "Publish";
        displayModal(action);
    });

    document.getElementById("sub").addEventListener("click", function() {
        action = "Subscribe";
        displayModal(action);
    });

    document.getElementById("unsub").addEventListener("click", function() {
        action = "Unsubscribe";
        displayModal(action);
    });

    document.getElementById("disconnect").addEventListener("click", function() {
        action = "Disconnect";
        displayModal(action);
    });

    document.getElementById("action").addEventListener("click", function() {
        performAction(action);
    });

    var clients = {};

    function performAction(action) {
        let ip = document.getElementById("addresses").value;
        let client_id = document.getElementById("client").value;
        let topic_id = document.getElementById("topic").value;
        let intervalStr = document.getElementById("interval").value;
        let interval = parseInt(intervalStr);

        switch (action) {
            case "Connect":
                if (clients[ip] != undefined &&
                    clients[ip][client_id] != undefined) break;

                if (client_id == "") {
                    client_id = "client_js_" + new Date().getTime();
                }
                clients[ip] = {};
                clients[ip][client_id] = new Paho.MQTT.Client(`ws://${ip}:9001/`, client_id);
                clients[ip][client_id].connect();
                break;
            case "Publish":
                if (clients[ip] == undefined || clients[ip][client_id] == undefined ||
                    topic_id == "" || isNaN(intervalStr)) break;

                if (clients[ip][client_id]["pub"]) {
                    clearInterval(clients[ip][client_id]["pub"]);
                }

                publish(clients[ip][client_id], topic_id, "init")
                clients[ip][client_id]["pub"] = setInterval(() => {
                    publish(clients[ip][client_id], topic_id, "test")
                }, interval);
                break;
            case "Subscribe":
                if (clients[ip] == undefined || clients[ip][client_id] == undefined ||
                    topic_id == "") break;

                clients[ip][client_id].subscribe(topic_id);
                break;
            case "Unsubscribe":
                if (clients[ip] == undefined || clients[ip][client_id] == undefined ||
                    topic_id == "") break;

                clients[ip][client_id].unsubscribe(topic_id);
                break;
            case "Disconnect":
                if (clients[ip] == undefined ||
                    clients[ip][client_id] == undefined) break;

                if (clients[ip][client_id]["pub"]) {
                    clearInterval(clients[ip][client_id]["pub"]);
                }

                clients[ip][client_id].disconnect();
                delete clients[ip][client_id];
                break;
            default:
                break;
        }
        console.log(client_id, topic_id, action);
        console.log(clients);
    }
});
