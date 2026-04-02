from PIL import Image, ImageDraw

def create_icon():
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    draw.ellipse([20, 20, 236, 236], fill='#409EFF', outline='#2080E0', width=3)
    
    draw.rectangle([60, 80, 196, 100], fill='white')
    draw.rectangle([60, 120, 196, 140], fill='white')
    draw.rectangle([60, 160, 196, 180], fill='white')
    
    draw.polygon([(180, 130), (220, 160), (180, 190)], fill='#67C23A')
    
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save('icon.ico', format='ICO', sizes=icon_sizes)
    print("图标已生成: icon.ico")

if __name__ == "__main__":
    create_icon()
