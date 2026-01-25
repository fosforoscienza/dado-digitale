let selectedQuestion = 0
let activeQuestion = -1
let waitingForResponses = false
let humanResponse = ""
let llmResponse = ""
const questions = [
    "Qual è il tuo ricordo più vivido dell'infanzia?",
    "Come spiegheresti la pioggia a un bambino?",
    "Se potessi cambiare una sola cosa del mondo, cosa sceglieresti?"
]
const llmResponses = [
    "Ricordo estati lunghe e il profumo dell'erba dopo il temporale.",
    "Direi che sono nuvole che si svuotano per dare acqua alla terra.",
    "Sceglierei più tempo per ascoltarci davvero."
]
function showQuestionPreview() {
    basic.showNumber(selectedQuestion + 1)
    serial.writeLine("Selezionata domanda " + (selectedQuestion + 1) + ": " + questions[selectedQuestion])
    serial.writeLine("Premi B per inviarla.")
}
function resetResponses() {
    humanResponse = ""
    llmResponse = ""
}
function checkCompletion() {
    if (waitingForResponses && humanResponse.length > 0 && llmResponse.length > 0) {
        waitingForResponses = false
        serial.writeLine("--- Risposte complete ---")
        serial.writeLine("LLM: " + llmResponse)
        serial.writeLine("Umano: " + humanResponse)
        serial.writeLine("Premi A per scegliere la prossima domanda.")
        basic.showIcon(IconNames.Yes)
    }
}
function sendQuestion() {
    if (waitingForResponses) {
        serial.writeLine("Una domanda è già in corso.")
        return
    }
    resetResponses()
    activeQuestion = selectedQuestion
    waitingForResponses = true
    basic.showNumber(activeQuestion + 1)
    serial.writeLine("--- Domanda " + (activeQuestion + 1) + " ---")
    serial.writeLine(questions[activeQuestion])
    serial.writeLine("Attendo la risposta umana dal secondo terminale...")
    control.inBackground(function () {
        basic.pause(40000)
        if (waitingForResponses && activeQuestion == selectedQuestion && llmResponse.length == 0) {
            llmResponse = llmResponses[activeQuestion]
            serial.writeLine("(40s) LLM: " + llmResponse)
            checkCompletion()
        }
    })
}
input.onButtonPressed(Button.A, function () {
    if (waitingForResponses) {
        serial.writeLine("Attendi le risposte prima di cambiare domanda.")
        return
    }
    selectedQuestion = (selectedQuestion + 1) % questions.length
    showQuestionPreview()
})
input.onButtonPressed(Button.B, function () {
    sendQuestion()
})
serial.onDataReceived(serial.delimiters(Delimiters.NewLine), function () {
    if (!waitingForResponses) {
        return
    }
    let incoming = serial.readLine().trim()
    if (incoming.length == 0) {
        return
    }
    if (humanResponse.length == 0) {
        humanResponse = incoming
        serial.writeLine("Umano: " + humanResponse)
        checkCompletion()
    }
})
serial.writeLine("Interfaccia Test di Turing")
serial.writeLine("Premi A per scegliere una domanda, B per inviarla.")
showQuestionPreview()
