🖼️ Background Remover GUI (Python)

A lightweight desktop application built with Python, Tkinter, and rembg that allows users to remove image backgrounds with a simple graphical interface.

The processed image is automatically saved as a transparent PNG file.

✨ Overview

This project provides an easy-to-use GUI for AI-powered background removal.
It is ideal for beginners learning Python GUI development and anyone who needs quick background removal without complex tools.

🚀 Features

Clean and simple Tkinter interface

Upload images from your system

AI-based background removal using rembg

Automatic export as transparent PNG

Live preview inside the application

Supports common image formats

🖥️ Demo Workflow

Launch the application

Click Upload Image

Select an image file

Background is removed automatically

Output is saved as:

original_filename_no_bg.png
🛠️ Tech Stack

Python 3.8+

Tkinter – GUI framework

rembg – AI background removal

Pillow (PIL) – Image processing

onnxruntime – Model inference backend

📦 Installation
1️⃣ Clone the Repository
git clone https://github.com/your-username/background-remover-gui.git
cd background-remover-gui
2️⃣ Install Dependencies
pip install rembg pillow onnxruntime

Or using Python module:

python -m pip install rembg pillow onnxruntime
▶️ Running the Application
python main.py
📁 Project Structure
background-remover-gui/
│
├── main.py
├── README.md
└── requirements.txt (optional)
📸 Supported Formats

PNG

JPG

JPEG

WEBP

🔮 Future Improvements

Drag & Drop support

Batch image processing

Custom output directory selection

Progress indicator

Modern styled UI (CustomTkinter)

Export as standalone executable (.exe)

📄 License

This project is open-source and available under the MIT License.

🤝 Contributing

Contributions are welcome.
Feel free to fork the repository and submit a pull request.

⭐ Support

If you found this project helpful, consider giving it a ⭐ on GitHub!
