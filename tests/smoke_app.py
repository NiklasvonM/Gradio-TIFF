"""
Minimal app for the smoke test.
"""

import gradio as gr
from gradio_tiff import Tiff

demo = gr.Interface(
    lambda x: x,
    inputs=Tiff(),
    outputs=Tiff(),
)

if __name__ == "__main__":
    demo.launch()
