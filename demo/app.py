import gradio as gr
from gradio_tiff import Tiff


# example = Tiff().example_value()

demo = gr.Interface(
    lambda x: x,
    inputs=Tiff(),
    outputs=Tiff(),
    # examples=[[example]],
)


if __name__ == "__main__":
    demo.launch()
