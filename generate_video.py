import cv2
import numpy as np

def generate_synthetic_cctv(filename="test_cctv.mp4", fps=20, seconds=4):
    width, height = 320, 240
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    # Base background (dark concrete channel banks)
    base_frame = np.zeros((height, width, 3), dtype=np.uint8)
    base_frame[:] = (40, 40, 40) # Dark gray concrete
    
    # Draw channel boundaries
    cv2.line(base_frame, (60, 0), (60, height), (80, 80, 80), 6)
    cv2.line(base_frame, (260, 0), (260, height), (80, 80, 80), 6)
    
    # Generate moving water particles/ripples
    num_particles = 80
    particles = np.random.rand(num_particles, 2) * np.array([width, height])
    flow_speed = np.array([0.0, 12.0]) # Flowing downwards
    
    for f in range(fps * seconds):
        frame = base_frame.copy()
        
        # Move particles downwards with minor turbulence
        particles += flow_speed + np.random.normal(0, 1.5, particles.shape)
        particles[:, 1] %= height # Loop back to top
        
        # Draw water texture inside the channel
        for p in particles:
            x, y = int(p[0]), int(p[1])
            if 60 < x < 260:
                cv2.circle(frame, (x, y), 2, (255, 180, 100), -1)
                
        # Overlay camera info & live timestamp
        cv2.putText(frame, f"CAM-03 ZOO ROAD | FRAME {f}", (10, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 255, 0), 1)
        
        out.write(frame)
        
    out.release()
    print(f"Successfully generated synthetic CCTV video: {filename}")

if __name__ == "__main__":
    generate_synthetic_cctv()