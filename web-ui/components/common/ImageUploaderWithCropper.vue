<template>
  <div class="space-y-3">
    <label class="archive-label">封面图</label>
    
    <div 
      v-if="!rawImageFile && !imageUrl"
      class="w-full h-48 bg-gray-700/50 rounded-md border-2 border-dashed border-gray-600 flex items-center justify-center relative cursor-pointer hover:border-cyan-500 transition-colors"
      @click="!disabled && triggerFileInput()"
      @dragover.prevent="!disabled && (isDragOver = true)"
      @dragleave.prevent="isDragOver = false"
      @drop.prevent="!disabled && onDrop($event)"
      :class="{ 'border-cyan-500': isDragOver, 'cursor-not-allowed opacity-50': disabled }"
    >
      <div class="text-center text-gray-500">
        <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
        <p class="mt-1 text-sm">{{ disabled ? '请先保存' : '点击或拖拽上传' }}</p>
      </div>
      <input ref="fileInput" type="file" class="hidden" accept="image/*" @change="onFileChange" :disabled="disabled">
    </div>

    <div v-if="imageUrl || rawImageFile" class="w-full h-48 bg-gray-900/50 rounded-md border border-gray-700 flex items-center justify-center relative overflow-hidden">
        <img :src="previewSrc" :key="previewSrc" class="max-h-full max-w-full object-contain" alt="Image Preview">
        <div v-if="isUploading" class="absolute inset-0 bg-black/70 flex flex-col items-center justify-center text-white">
            <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-cyan-500"></div>
            <p class="mt-2 text-sm">正在上传...</p>
        </div>
        <div v-if="rawImageFile && !isUploading" class="absolute bottom-2 left-2 right-2 flex justify-center gap-2">
            <button @click="handleDirectUse" class="btn btn-primary bg-green-600 hover:bg-green-500 text-xs !px-3 !py-1">直接使用</button>
            <button @click="isCropperOpen = true" class="btn btn-secondary text-xs !px-3 !py-1">裁剪图片</button>
        </div>
    </div>
    <div v-if="imageUrl || rawImageFile" class="flex justify-between items-center text-xs">
      <p class="text-gray-400 truncate max-w-[70%]">{{ rawImageFile?.name || '当前图片' }}</p>
      <button type="button" @click="clearImage" class="text-red-400 hover:underline">移除图片</button>
    </div>

    <Teleport to="body">
        <div v-if="isCropperOpen && rawImageForCropper" class="fixed inset-0 bg-black/80 flex items-center justify-center z-[60]">
            <div class="w-full max-w-2xl bg-gray-800 rounded-lg shadow-xl border border-gray-700 flex flex-col max-h-[90vh]">
                <header class="p-4 border-b border-gray-700 shrink-0">
                    <h3 class="font-semibold text-white">{{ cropperTitle }}</h3>
                </header>
                <main class="p-4 flex-grow min-h-0 overflow-y-hidden">
                    <vue-cropper 
                      v-if="cropperKey > 0"
                      ref="cropper" 
                      :src="rawImageForCropper" 
                      :aspect-ratio="imageAspectRatio" 
                      :view-mode="1" drag-mode="move" :auto-crop-area="0.8" :background="false" 
                      class="h-full w-full"
                    ></vue-cropper>
                </main>
                <footer class="p-4 border-t border-gray-700 flex justify-between items-center shrink-0">
                    <div class="flex gap-2">
                        <button @click="setAspectRatio(NaN)" class="btn btn-secondary text-xs" :class="{'bg-gray-600': isNaN(imageAspectRatio)}">自由</button>
                        <button @click="setAspectRatio(1)" class="btn btn-secondary text-xs" :class="{'bg-gray-600': imageAspectRatio === 1}">1:1</button>
                        <button @click="setAspectRatio(2/3)" class="btn btn-secondary text-xs" :class="{'bg-gray-600': imageAspectRatio === 2/3}">2:3</button>
                        <button @click="setAspectRatio(16/9)" class="btn btn-secondary text-xs" :class="{'bg-gray-600': imageAspectRatio === 16/9}">16:9</button>
                    </div>
                    <div class="flex gap-3">
                        <button @click="isCropperOpen = false" class="btn btn-secondary">取消</button>
                        <button @click="cropAndUploadImage" class="btn btn-primary bg-cyan-600 hover:bg-cyan-500">确认并上传</button>
                    </div>
                </footer>
            </div>
        </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick, type PropType } from 'vue';
import VueCropper from 'vue-cropperjs';
import 'cropperjs/dist/cropper.css';
import { useUIStore } from '~/stores/ui';
import { processImageForUpload } from '~/utils/imageProcessor';

const props = defineProps({
  imageUrl: { type: String as PropType<string | null>, default: null },
  aspectRatio: { type: Number, default: NaN },
  cropperTitle: { type: String, default: '裁剪图片' },
  uploadFunction: { type: Function as PropType<(blob: Blob) => Promise<string>>, required: true },
  disabled: { type: Boolean, default: false }
});

const emit = defineEmits(['update:imageUrl']);

const uiStore = useUIStore();
const rawImageFile = ref<File | null>(null);
const rawImageForCropper = ref<string | null>(null);
const isUploading = ref(false);

const fileInput = ref<HTMLInputElement | null>(null);
const isCropperOpen = ref(false);
const isDragOver = ref(false);
const cropper = ref<any>(null);
const cropperKey = ref(0);
const imageAspectRatio = ref<number>(props.aspectRatio);

const previewSrc = computed(() => {
    const url = rawImageForCropper.value || props.imageUrl;
    return url === null ? undefined : url;
});

watch(() => props.disabled, (isDisabled) => { if(isDisabled) clearImage(); });

const triggerFileInput = () => fileInput.value?.click();

const onFileChange = (e: Event) => {
    const target = e.target as HTMLInputElement;
    if (target.files && target.files[0]) processFile(target.files[0]);
};

const onDrop = (e: DragEvent) => {
    isDragOver.value = false;
    if (e.dataTransfer?.files && e.dataTransfer.files[0]) processFile(e.dataTransfer.files[0]);
};

const processFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
        uiStore.setGlobalError('请上传图片文件。');
        return;
    }
    rawImageFile.value = file;
    const reader = new FileReader();
    reader.onload = (e) => { 
        rawImageForCropper.value = e.target?.result as string;
    };
    reader.readAsDataURL(file);
};

const clearImage = () => {
    rawImageFile.value = null;
    rawImageForCropper.value = null;
    imageAspectRatio.value = props.aspectRatio;
    emit('update:imageUrl', null);
    if (fileInput.value) fileInput.value.value = '';
};

async function uploadFile(file: File | Blob) {
    isUploading.value = true;
    try {
        const processedBlob = await processImageForUpload(file instanceof File ? file : new File([file], "image.webp", {type: "image.webp"}));
        const newUrl = await props.uploadFunction(processedBlob);
        emit('update:imageUrl', newUrl);
        rawImageFile.value = null;
        rawImageForCropper.value = null;
    } catch (error) {
        uiStore.setGlobalError(`图片上传失败: ${error}`);
    } finally {
        isUploading.value = false;
    }
}

async function handleDirectUse() {
    if (rawImageFile.value) await uploadFile(rawImageFile.value);
}

const cropAndUploadImage = async () => {
    if (cropper.value) {
        const canvas = cropper.value.getCroppedCanvas({ maxWidth: 4096, maxHeight: 4096, imageSmoothingQuality: 'high' });
        canvas.toBlob(async (blob: Blob | null) => {
            if (blob) {
                isCropperOpen.value = false;
                await uploadFile(blob);
            } else {
                uiStore.setGlobalError("裁剪失败：无法生成图片数据。");
            }
        }, 'image/webp', 0.92);
    }
};

watch(isCropperOpen, (isOpen) => {
    if (isOpen) {
        imageAspectRatio.value = props.aspectRatio;
        cropperKey.value++;
    }
});

async function setAspectRatio(ratio: number) {
    imageAspectRatio.value = ratio;
    cropperKey.value = 0;
    await nextTick();
    cropperKey.value = 1;
}
</script>

<style>
.cropper-view-box, .cropper-face { border-radius: inherit; }
</style>