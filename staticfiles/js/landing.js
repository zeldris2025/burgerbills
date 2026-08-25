(() => {
    const container = document.getElementById('burger-scene');
    if (!container || !window.THREE) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    camera.position.set(0, 0, 11.5);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    const burger = new THREE.Group();
    burger.rotation.set(-0.08, -0.28, -0.04);
    scene.add(burger);

    function makeSurfaceTexture(scale, contrast) {
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 128;
        const context = canvas.getContext('2d');
        const image = context.createImageData(canvas.width, canvas.height);
        for (let y = 0; y < canvas.height; y += 1) {
            for (let x = 0; x < canvas.width; x += 1) {
                const offset = (y * canvas.width + x) * 4;
                const grain = (Math.sin(x * 1.73 + y * 2.41) + Math.sin(x * 0.29 - y * 0.47)) * contrast;
                const value = Math.max(0, Math.min(255, 128 + grain));
                image.data[offset] = value;
                image.data[offset + 1] = value;
                image.data[offset + 2] = value;
                image.data[offset + 3] = 255;
            }
        }
        context.putImageData(image, 0, 0);
        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(scale, scale);
        return texture;
    }

    function makeColorTexture(scale, baseColor, variance, contrast, size = 128) {
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const context = canvas.getContext('2d');
        const image = context.createImageData(canvas.width, canvas.height);
        const red = (baseColor >> 16) & 255;
        const green = (baseColor >> 8) & 255;
        const blue = baseColor & 255;
        for (let y = 0; y < canvas.height; y += 1) {
            for (let x = 0; x < canvas.width; x += 1) {
                const offset = (y * canvas.width + x) * 4;
                const grain = (Math.sin(x * 1.51 + y * 2.07) + Math.sin(x * 0.31 - y * 0.53)) * contrast;
                const speckle = (Math.random() - 0.5) * variance;
                const lum = grain + speckle;
            image.data[offset] = Math.max(0, Math.min(255, red + lum));
            image.data[offset + 1] = Math.max(0, Math.min(255, green + lum * 0.92));
            image.data[offset + 2] = Math.max(0, Math.min(255, blue + lum * 0.8));
                image.data[offset + 3] = 255;
            }
        }
        context.putImageData(image, 0, 0);
        const texture = new THREE.CanvasTexture(canvas);
        texture.colorSpace = THREE.SRGBColorSpace;
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(scale, scale);
        return texture;
    }

    const breadTexture = makeSurfaceTexture(3.5, 18);
    const meatTexture = makeSurfaceTexture(5.5, 42);
    const bunCutColorMap = makeColorTexture(3.5, 0xecc07f, 16, 8);
    const meatColorMap = makeColorTexture(5.5, 0x4a2015, 30, 26);
    const cheeseColorMap = makeColorTexture(2.5, 0xf3ac1e, 18, 10);
    const lettuceColorMap = makeColorTexture(4, 0x4f8f3c, 24, 12);
    const tomatoColorMap = makeColorTexture(3, 0xd8452a, 14, 9);

    const makeMaterial = (color, roughness = 0.72, options = {}) => (
        new THREE.MeshPhysicalMaterial({ color, roughness, ...options })
    );
    const bun = makeMaterial(0xc98235, 0.7, {
        bumpMap: breadTexture,
        bumpScale: 0.035,
        clearcoat: 0.06,
        clearcoatRoughness: 0.82,
        side: THREE.DoubleSide,
        transparent: false,
        opacity: 1,
        transmission: 0
    });
    const bunCut = makeMaterial(0xffffff, 0.68, {
        map: bunCutColorMap,
        bumpMap: breadTexture,
        bumpScale: 0.028
    });
    const patty = makeMaterial(0xffffff, 0.82, {
        map: meatColorMap,
        bumpMap: meatTexture,
        bumpScale: 0.16,
        clearcoat: 0.3,
        clearcoatRoughness: 0.45
    });
    const cheese = makeMaterial(0xffffff, 0.42, {
        map: cheeseColorMap,
        side: THREE.DoubleSide,
        clearcoat: 0.4,
        clearcoatRoughness: 0.3
    });
    const lettuce = makeMaterial(0xffffff, 0.85, { map: lettuceColorMap, side: THREE.DoubleSide });
    const tomato = makeMaterial(0xffffff, 0.55, { map: tomatoColorMap, clearcoat: 0.35, clearcoatRoughness: 0.25 });
    const onion = makeMaterial(0xe0b2c4, 0.4, { transparent: true, opacity: 0.85, clearcoat: 0.5, clearcoatRoughness: 0.2 });

    function addLayer(geometry, layerMaterial, height, scale = 1, rotation = 0) {
        const mesh = new THREE.Mesh(geometry, layerMaterial);
        mesh.position.y = height;
        mesh.scale.set(scale, 1, scale);
        mesh.rotation.y = rotation;
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        burger.add(mesh);
        return mesh;
    }

    function makeNaturalLayer(radiusTop, radiusBottom, height, edgeAmount, waves = 7) {
        const geometry = new THREE.CylinderGeometry(radiusTop, radiusBottom, height, 64, 4);
        const positions = geometry.attributes.position;
        for (let index = 0; index < positions.count; index += 1) {
            const x = positions.getX(index);
            const z = positions.getZ(index);
            const angle = Math.atan2(z, x);
            const edge = 1 + Math.sin(angle * waves + 0.7) * edgeAmount
                + Math.sin(angle * (waves + 3)) * edgeAmount * 0.35;
            positions.setX(index, x * edge);
            positions.setZ(index, z * edge);
        }
        geometry.computeVertexNormals();
        return geometry;
    }

    const bottomBunProfile = [
        new THREE.Vector2(0, -0.3),
        new THREE.Vector2(1.72, -0.3),
        new THREE.Vector2(2.18, -0.23),
        new THREE.Vector2(2.38, 0),
        new THREE.Vector2(2.32, 0.25),
        new THREE.Vector2(2.08, 0.36),
        new THREE.Vector2(0, 0.36)
    ];
    addLayer(new THREE.LatheGeometry(bottomBunProfile, 64), bunCut, -1.84);
    addLayer(makeNaturalLayer(2.35, 2.35, 0.13, 0.075, 9), lettuce, -1.49, 1, 0.08);
    addLayer(makeNaturalLayer(2.2, 2.25, 0.58, 0.022, 11), patty, -1.18, 1, -0.06);

    const cheeseGeometry = new THREE.PlaneGeometry(3.75, 3.75, 8, 8);
    cheeseGeometry.rotateX(-Math.PI / 2);
    const cheesePositions = cheeseGeometry.attributes.position;
    for (let index = 0; index < cheesePositions.count; index += 1) {
        const x = cheesePositions.getX(index);
        const z = cheesePositions.getZ(index);
        const edgeDistance = Math.max(Math.abs(x), Math.abs(z));
        const edgeDrop = Math.max(0, edgeDistance - 1.3) * 0.34;
        cheesePositions.setY(index, -edgeDrop + Math.sin(x * 2.2 + z) * 0.025);
    }
    cheeseGeometry.computeVertexNormals();
    addLayer(makeNaturalLayer(1.9, 1.9, 0.12, 0.01, 6), cheese, -0.86, 1, 0.08);
    addLayer(cheeseGeometry, cheese, -0.82, 1, Math.PI / 4 + 0.08);

    addLayer(makeNaturalLayer(2.02, 2.02, 0.2, 0.012, 6), tomato, -0.78, 1, 0.04);
    const onionOuter = addLayer(new THREE.TorusGeometry(1.46, 0.1, 12, 56), onion, -0.64, 1, -0.15);
    const onionInner = addLayer(new THREE.TorusGeometry(0.92, 0.08, 10, 48), onion, -0.62, 1, 0.18);
    onionOuter.rotation.x = Math.PI / 2;
    onionInner.rotation.x = Math.PI / 2;
    addLayer(makeNaturalLayer(2.32, 2.32, 0.16, 0.08, 10), lettuce, -0.5, 1, -0.1);
    addLayer(makeNaturalLayer(2.28, 2.36, 0.42, 0.008, 8), bunCut, -0.3);

    const topBunProfile = [
        new THREE.Vector2(0, 2.02),
        new THREE.Vector2(0.55, 1.98),
        new THREE.Vector2(1.18, 1.78),
        new THREE.Vector2(1.75, 1.43),
        new THREE.Vector2(2.16, 0.95),
        new THREE.Vector2(2.38, 0.42),
        new THREE.Vector2(2.34, 0.12),
        new THREE.Vector2(0, 0.12)
    ];
    addLayer(new THREE.LatheGeometry(topBunProfile, 64), bun, -0.22);

    const charMaterial = makeMaterial(0x24120a, 0.92, { clearcoat: 0.15, clearcoatRoughness: 0.5 });
    [-0.85, -0.28, 0.34, 0.92].forEach((x, index) => {
        const charMark = new THREE.Mesh(new THREE.BoxGeometry(0.055, 0.32, 0.035), charMaterial);
        charMark.position.set(x, -1.14 + (index % 2) * 0.07, 2.22);
        charMark.rotation.z = -0.32;
        burger.add(charMark);
    });

    const seedMaterials = [
        makeMaterial(0xf7d792, 0.78),
        makeMaterial(0xecc47f, 0.85),
        makeMaterial(0xf9e2a8, 0.72)
    ];
    const seedGeometry = new THREE.SphereGeometry(1, 12, 8);
    const seedPositions = [
        [-1.35, 0.28], [-1.08, 0.72], [-0.72, 1.04], [-0.3, 1.24], [0.16, 1.2],
        [0.62, 1.06], [1.04, 0.76], [1.36, 0.34], [-1.55, -0.2], [-1.22, -0.48],
        [-0.82, -0.7], [-0.38, -0.82], [0.08, -0.8], [0.54, -0.72], [0.96, -0.5],
        [1.42, -0.18], [-0.82, 0.46], [-0.42, 0.68], [0.02, 0.76], [0.46, 0.64],
        [0.86, 0.4], [-1.04, -0.04], [-0.62, 0.06], [-0.2, 0.18], [0.24, 0.12],
        [0.7, 0.02], [1.08, -0.12], [-0.48, -0.34], [0.02, -0.3], [0.5, -0.3]
    ];
    seedPositions.forEach(([x, z], index) => {
        const domeRadius = 2.5;
        const surfaceY = 0.02 + Math.sqrt(Math.max(0, domeRadius ** 2 - x ** 2 - z ** 2)) * 0.72;
        const normal = new THREE.Vector3(x, (surfaceY - 0.02) / 0.72, z).normalize();
        const seed = new THREE.Mesh(seedGeometry, seedMaterials[index % seedMaterials.length]);
        seed.scale.set(0.042, 0.022, 0.115);
        seed.position.set(x, surfaceY + 0.014, z);
        seed.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);
        seed.rotateY(index * 1.7 + 0.35);
        seed.castShadow = true;
        burger.add(seed);
    });

    const keyLight = new THREE.DirectionalLight(0xffd591, 4.2);
    keyLight.position.set(-4, 7, 8);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(1024, 1024);
    keyLight.shadow.radius = 4;
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0xf04c2e, 3.5);
    rimLight.position.set(5, 2, -4);
    scene.add(rimLight);
    scene.add(new THREE.HemisphereLight(0xffe7bf, 0x24130c, 2.2));

    const fillLight = new THREE.PointLight(0xfff2d8, 1.4, 20, 2);
    fillLight.position.set(2.5, 3.5, 6);
    scene.add(fillLight);

    const shadow = new THREE.Mesh(
        new THREE.CircleGeometry(3.5, 64),
        new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.28 })
    );
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.y = -2.58;
    shadow.scale.y = 0.42;
    scene.add(shadow);

    let pointerX = 0;
    let pointerY = 0;
    container.addEventListener('pointermove', (event) => {
        const bounds = container.getBoundingClientRect();
        pointerX = ((event.clientX - bounds.left) / bounds.width - 0.5) * 0.7;
        pointerY = ((event.clientY - bounds.top) / bounds.height - 0.5) * 0.35;
    });
    container.addEventListener('pointerleave', () => {
        pointerX = 0;
        pointerY = 0;
    });

    function resize() {
        const width = container.clientWidth;
        const height = container.clientHeight;
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    }
    window.addEventListener('resize', resize);
    resize();

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function render(time = 0) {
        const turntableRotation = reduceMotion ? -0.28 : -0.28 + time * 0.00022;
        const targetY = turntableRotation + pointerX;
        const targetX = -0.08 - pointerY;
        burger.rotation.y += (targetY - burger.rotation.y) * 0.04;
        burger.rotation.x += (targetX - burger.rotation.x) * 0.04;
        if (!reduceMotion) burger.position.y = Math.sin(time * 0.00085) * 0.12;
        renderer.render(scene, camera);
        requestAnimationFrame(render);
    }
    render();
})();