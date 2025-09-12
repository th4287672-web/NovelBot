// web-ui/utils/imageProcessor.ts

/**
 * 客户端图片预处理器
 * @param file 原始图片文件 (File 对象)
 * @param maxWidth 最大宽度，默认 1280px
 * @param maxHeight 最大高度，默认 1280px
 * @param quality WebP 格式的输出质量 (0.0 - 1.0)，默认 0.92
 * @returns 返回一个优化后的图片 Blob 对象
 */
export function processImageForUpload(
  file: File,
  maxWidth: number = 1280,
  maxHeight: number = 1280,
  quality: number = 0.92
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = (event) => {
      const img = new Image();
      img.src = event.target?.result as string;
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        if (!ctx) {
          return reject(new Error('无法获取 Canvas 绘图上下文'));
        }

        let { width, height } = img;

        if (width > height) {
          if (width > maxWidth) {
            height = Math.round(height * (maxWidth / width));
            width = maxWidth;
          }
        } else {
          if (height > maxHeight) {
            width = Math.round(width * (maxHeight / height));
            height = maxHeight;
          }
        }

        canvas.width = width;
        canvas.height = height;

        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob);
            } else {
              reject(new Error('Canvas 转换为 Blob 失败'));
            }
          },
          'image/webp',
          quality
        );
      };
      img.onerror = (error) => reject(error);
    };
    reader.onerror = (error) => reject(error);
  });
}