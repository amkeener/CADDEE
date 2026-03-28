import { useRef, useEffect } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { STLLoader } from 'three/addons/loaders/STLLoader.js'

interface ViewportProps {
  stlData: ArrayBuffer | null
  isCompiling: boolean
}

const BACKGROUND_COLOR = 0x1a1a2e
const COLOR_STABLE = 0x888888
const COLOR_COMPILING = 0xffcc00

export function Viewport({ stlData, isCompiling }: ViewportProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const controlsRef = useRef<OrbitControls | null>(null)
  const meshRef = useRef<THREE.Mesh | null>(null)
  const frameIdRef = useRef<number>(0)

  // ── Scene initialization & cleanup ──
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Scene
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(BACKGROUND_COLOR)
    sceneRef.current = scene

    // Camera
    const camera = new THREE.PerspectiveCamera(
      50,
      container.clientWidth / container.clientHeight,
      0.1,
      2000
    )
    camera.position.set(0, 50, 100)
    cameraRef.current = camera

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setPixelRatio(window.devicePixelRatio)
    renderer.setSize(container.clientWidth, container.clientHeight)
    container.appendChild(renderer.domElement)
    rendererRef.current = renderer

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0)
    directionalLight.position.set(50, 100, 80)
    scene.add(directionalLight)

    // A secondary fill light from the opposite side to reduce harsh shadows
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.3)
    fillLight.position.set(-50, -20, -60)
    scene.add(fillLight)

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.1
    controls.enableRotate = true
    controls.enablePan = true
    controls.enableZoom = true
    controlsRef.current = controls

    // Animation loop
    function animate() {
      frameIdRef.current = requestAnimationFrame(animate)
      controls.update()
      renderer.render(scene, camera)
    }
    animate()

    // Resize observer — more reliable than window resize for flex containers
    const resizeObserver = new ResizeObserver(() => {
      const width = container.clientWidth
      const height = container.clientHeight
      if (width === 0 || height === 0) return

      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height)
    })
    resizeObserver.observe(container)

    // Cleanup on unmount
    return () => {
      resizeObserver.disconnect()
      cancelAnimationFrame(frameIdRef.current)
      controls.dispose()
      renderer.dispose()

      // Dispose mesh if present
      if (meshRef.current) {
        meshRef.current.geometry.dispose()
        const mat = meshRef.current.material
        if (Array.isArray(mat)) {
          mat.forEach((m) => m.dispose())
        } else {
          mat.dispose()
        }
        meshRef.current = null
      }

      // Remove the canvas from the DOM
      if (renderer.domElement.parentElement) {
        renderer.domElement.parentElement.removeChild(renderer.domElement)
      }

      sceneRef.current = null
      cameraRef.current = null
      rendererRef.current = null
      controlsRef.current = null
    }
  }, [])

  // ── STL data loading & hot-swap ──
  useEffect(() => {
    const scene = sceneRef.current
    const camera = cameraRef.current
    const controls = controlsRef.current
    if (!scene || !camera || !controls) return

    // Dispose previous mesh
    if (meshRef.current) {
      scene.remove(meshRef.current)
      meshRef.current.geometry.dispose()
      const mat = meshRef.current.material
      if (Array.isArray(mat)) {
        mat.forEach((m) => m.dispose())
      } else {
        mat.dispose()
      }
      meshRef.current = null
    }

    if (!stlData) return

    // Parse STL
    const loader = new STLLoader()
    const geometry = loader.parse(stlData)
    geometry.computeVertexNormals()

    // Material — pick color based on current compile state
    const material = new THREE.MeshStandardMaterial({
      color: isCompiling ? COLOR_COMPILING : COLOR_STABLE,
      metalness: 0.2,
      roughness: 0.6,
      flatShading: false,
    })

    const mesh = new THREE.Mesh(geometry, material)
    scene.add(mesh)
    meshRef.current = mesh

    // Auto-fit camera to model
    fitCameraToObject(camera, controls, mesh)
  }, [stlData])

  // ── Compile-state color feedback ──
  useEffect(() => {
    const mesh = meshRef.current
    if (!mesh) return

    const material = mesh.material as THREE.MeshStandardMaterial
    material.color.set(isCompiling ? COLOR_COMPILING : COLOR_STABLE)
  }, [isCompiling])

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        overflow: 'hidden',
      }}
    />
  )
}

/**
 * Positions the camera so the entire object is visible, using
 * the geometry bounding box and the camera's field of view.
 */
function fitCameraToObject(
  camera: THREE.PerspectiveCamera,
  controls: OrbitControls,
  object: THREE.Mesh
) {
  const box = new THREE.Box3().setFromObject(object)
  const size = box.getSize(new THREE.Vector3())
  const center = box.getCenter(new THREE.Vector3())

  // Determine the maximum dimension to base distance on
  const maxDim = Math.max(size.x, size.y, size.z)
  const fovRad = camera.fov * (Math.PI / 180)
  // Distance needed so the object fills roughly 75% of the vertical FOV
  let cameraDistance = (maxDim / 2) / Math.tan(fovRad / 2)
  cameraDistance *= 1.35 // padding factor

  // Position camera looking from a 3/4 angle
  const direction = new THREE.Vector3(0.5, 0.35, 1).normalize()
  camera.position.copy(center).addScaledVector(direction, cameraDistance)
  camera.lookAt(center)

  // Update near/far planes based on model size
  camera.near = cameraDistance * 0.01
  camera.far = cameraDistance * 10
  camera.updateProjectionMatrix()

  // Point orbit controls at the center of the model
  controls.target.copy(center)
  controls.update()
}
