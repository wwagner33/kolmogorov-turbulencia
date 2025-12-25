import os

import matplotlib

matplotlib.use("TkAgg")

from datetime import datetime

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pygame

agora = datetime.now()
timestamp = agora.strftime("%Y%m%d_%H%M")

VIDEO_FILE_NAME = f"simulacao-{timestamp}.mp4"
CAPTURAS_PATH = "capturas"


def criar_video(pasta_origem, nome_video_saida, fps=30):
    image_folder = pasta_origem
    video_name = nome_video_saida

    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    images.sort()

    if not images:
        print(f"Nenhuma imagem encontrada em {image_folder}")
        return

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))

    print(f"Gerando vídeo '{video_name}' com {len(images)} frames...")

    for image in images:
        video.write(cv2.imread(os.path.join(image_folder, image)))

    cv2.destroyAllWindows()
    video.release()
    print("Vídeo concluído com sucesso!")


# MOTOR DE FÍSICA (Compartilhado)
class KolmogorovField:
    def __init__(self, N=512, slope=2.0):
        self.N = N
        # Configurar grade de frequência
        kx = np.fft.fftfreq(N)
        ky = np.fft.fftfreq(N)
        kx_grid, ky_grid = np.meshgrid(kx, ky)
        k = np.sqrt(kx_grid**2 + ky_grid**2)
        k[0, 0] = 1.0

        # Amplitude fixa baseada na lei de potência
        self.amplitude = k ** (-slope / 2.0)
        self.amplitude[0, 0] = 0

        # Estado inicial
        self.fase = 2 * np.pi * np.random.rand(N, N)

    def get_velocity_field(self):
        """Retorna os vetores U e V do campo atual"""
        # Gerar campo complexo
        campo_freq = self.amplitude * np.exp(1j * self.fase)
        psi = np.real(np.fft.ifft2(campo_freq))

        # Normalizar função de corrente
        psi = (psi - psi.mean()) / psi.std()

        # Calcular velocidades (Rotacional)
        v_y, v_x = np.gradient(psi)
        u = -v_y * 50.0  # Fator de escala para velocidade visual
        v = v_x * 50.0
        return u, v, psi

    def get_spectrum(self, psi):
        """Cálculo estatístico para o gráfico"""
        fourier = np.fft.fftshift(np.fft.fft2(psi))
        psd = np.abs(fourier) ** 2

        y, x = np.indices((self.N, self.N))
        center = np.array([self.N // 2, self.N // 2])
        r = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2).astype(int)

        tbin = np.bincount(r.ravel(), psd.ravel())
        nr = np.bincount(r.ravel())
        radial_profile = tbin / np.maximum(nr, 1)
        return radial_profile


# A PROVA CIENTÍFICA
def mostrar_grafico_estatico(motor):
    print("Gerando gráfico de análise e salvando como 'espectro_kolmogorov.png'...")
    u, v, psi = motor.get_velocity_field()
    spectrum = motor.get_spectrum(psi)
    k_axis = np.arange(len(spectrum))

    plt.figure(figsize=(8, 6))
    start, end = 5, 100

    # Plotar dados
    plt.loglog(k_axis[start:end], spectrum[start:end], "c-", lw=2, label="Simulação")

    # Plotar Teoria
    teoria = k_axis[start:end] ** -2.6  # Slope ajustado
    scale = spectrum[start] / teoria[0]
    plt.loglog(k_axis[start:end], teoria * scale, "r--", label="Teoria de Kolmogorov")

    plt.title("Validação Matemática: Espectro de Energia")
    plt.xlabel("Frequência Espacial (k)")
    plt.ylabel("Energia E(k)")
    plt.legend()
    plt.grid(True, which="both", alpha=0.3)

    # EM VEZ DE plt.show(), USAMOS SAVEFIG
    plt.savefig("espectro_kolmogorov.png")
    print("Gráfico salvo! Iniciando simulação visual...")
    plt.close()  # Fecha a figura para liberar memória


# A SIMULAÇÃO VISUAL
def rodar_simulacao_pygame(motor):
    # Configurações
    WIDTH, HEIGHT = 800, 800
    NUM_PARTICLES = 10000
    BACKGROUND_COLOR = (5, 5, 20)  # Azul noturno profundo

    # Paleta Van Gogh (Azul -> Ciano -> Amarelo)
    COLORS = [
        (28, 63, 117),  # Azul Médio
        (86, 152, 196),  # Ciano
        (232, 216, 74),  # Amarelo Ouro
    ]

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Van Gogh Turbulence - Physics Simulation")
    clock = pygame.time.Clock()

    # Gerar campo de velocidade inicial
    # Interpolamos o campo N x N para o tamanho da tela WIDTH x HEIGHT
    print("Calculando campo de vetores...")
    u_grid, v_grid, _ = motor.get_velocity_field()

    # Criar partículas (Posições aleatórias)
    particles = np.random.rand(NUM_PARTICLES, 2) * [WIDTH, HEIGHT]

    # CONFIGURAÇÃO

    pausado = False
    gravado = False
    contador_frames = 0
    nome_pasta = "capturas"
    running = True

    if not os.path.exists(nome_pasta):
        os.makedirs(nome_pasta)
    pygame.font.init()
    fonte_ui = pygame.font.SysFont("Arial", 24)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = not running
                elif event.key == pygame.K_SPACE:
                    pausado = not pausado
                elif event.key == pygame.K_s:
                    gravado = not gravado
                    if gravado:
                        print("Gravação iniciada...")
                    else:
                        print("Gravação finalizada.\n")
                        print("Criando arquivo de vídeo da simulação...")
                        criar_video(CAPTURAS_PATH, VIDEO_FILE_NAME, fps=60)

        if not pausado:
            #  Lógica de Física (Lagrangiana)
            # 1. Encontrar em qual célula da grade cada partícula está
            # (Mapear posição da tela 800x800 para grade 512x512)
            grid_x = (particles[:, 0] / WIDTH * motor.N).astype(int) % motor.N
            grid_y = (particles[:, 1] / HEIGHT * motor.N).astype(int) % motor.N

            # 2. Obter velocidade naquela célula (Vectorized Lookup)
            # Isso é super rápido com Numpy
            p_u = u_grid[grid_y, grid_x]
            p_v = v_grid[grid_y, grid_x]

            # 3. Mover partículas
            particles[:, 0] += p_u * 0.1  # dt
            particles[:, 1] += p_v * 0.1

            # 4. Wrap-around (Toroidal) - Se sair da tela, volta do outro lado
            particles[:, 0] = particles[:, 0] % WIDTH
            particles[:, 1] = particles[:, 1] % HEIGHT

            # --- Renderização ---
            # Técnica de "Trail": Em vez de limpar a tela, desenhamos um retângulo
            # preto semi-transparente. Isso deixa o rastro das partículas.
            fade_surface = pygame.Surface((WIDTH, HEIGHT))
            fade_surface.set_alpha(
                20
            )  # Transparência (0-255). Menor = rastros mais longos
            fade_surface.fill(BACKGROUND_COLOR)
            screen.blit(fade_surface, (0, 0))

            # Desenhar partículas
            # Colorimos baseados na velocidade
            speeds = np.sqrt(p_u**2 + p_v**2)
            max_speed = np.percentile(speeds, 95)  # Normalizar ignorando outliers

            # Acesso direto aos pixels (muito mais rápido que desenhar circulos)
            pixel_array = pygame.surfarray.pixels3d(screen)

            # Mapeamento simples de cor (Apenas para demonstração visual rápida)
            # Partículas rápidas = Amarelo, Lentas = Azul
            for i in range(NUM_PARTICLES):
                x, y = int(particles[i, 0]), int(particles[i, 1])
                speed_ratio = min(speeds[i] / max_speed, 1.0)

                # Escolher cor baseada na velocidade
                if speed_ratio > 0.6:
                    c = COLORS[2]  # Amarelo
                elif speed_ratio > 0.3:
                    c = COLORS[1]  # Ciano
                else:
                    c = COLORS[0]  # Azul

                # Desenhar (verificando limites por segurança)
                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                    pixel_array[x, y] = c
            del pixel_array  # Liberar trava da superfície

            pass

        if pausado:
            texto_pausa = fonte_ui.render(
                "PAUSADO", True, (255, 0, 0)
            )  # Texto Vermelho
            screen.blit(texto_pausa, (10, 10))

        if gravado:
            # Indicador visual de gravação (círculo vermelho no canto)
            pygame.draw.circle(screen, (255, 0, 0), (WIDTH - 20, 20), 10)

            # Lógica de Salvar o Frame
            nome_arquivo = f"{nome_pasta}/img_{contador_frames:05d}.png"
            pygame.image.save(screen, nome_arquivo)
            contador_frames += 1

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    # 1. Configurar Física
    motor_fisico = KolmogorovField(N=512, slope=2.0)

    # 2. Mostrar Análise Matemática
    mostrar_grafico_estatico(motor_fisico)

    # 3. Iniciar Simulação Interativa
    rodar_simulacao_pygame(motor_fisico)
