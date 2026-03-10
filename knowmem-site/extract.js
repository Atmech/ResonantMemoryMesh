const fs = require('fs');
const pdf = require('pdf-parse');

let dataBuffer = fs.readFileSync('../docs/Resonance is All You Need_ A Dynamical Systems Approach to Associative Memory Retrieval.pdf');

pdf(dataBuffer).then(function(data) {
    fs.writeFileSync('../docs/paper_text.txt', data.text);
    console.log("Success");
}).catch(err => console.error(err));
