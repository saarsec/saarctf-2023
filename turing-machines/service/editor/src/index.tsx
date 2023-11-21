//import React from 'react';
//import ReactDOM from 'react-dom/client';
import r2wc from "@r2wc/react-to-web-component";
import Editor from "./Editor";

const editorElement = r2wc(Editor, {props: {machine: "json", name: "string"}});
customElements.define("turingmachine-editor", editorElement);

/*
const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
);
root.render(
    <React.StrictMode>
        <div className="container">
            <Editor machine={[]} name="test"></Editor>
        </div>
    </React.StrictMode>
);
// */
