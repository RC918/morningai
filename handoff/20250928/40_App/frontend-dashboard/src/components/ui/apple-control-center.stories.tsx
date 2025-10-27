import type { Meta, StoryObj } from '@storybook/react'
import { AppleControlCenter, type Control } from './apple-control-center'
import { 
  Wifi, 
  Bluetooth, 
  Volume2, 
  Sun, 
  Moon, 
  Plane, 
  Music, 
  Camera,
  Flashlight,
  Lock,
  Timer,
  Calculator,
  Play,
  Pause,
  SkipForward,
  SkipBack
} from 'lucide-react'
import { useEffect } from 'react'

const meta = {
  title: 'Apple Design System/AppleControlCenter',
  component: AppleControlCenter.Provider,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'iOS-style Control Center component for quick access to system controls and settings. Features grid layout, long-press actions, and customizable controls.'
      }
    }
  },
  tags: ['autodocs']
} satisfies Meta<typeof AppleControlCenter.Provider>

export default meta
type Story = StoryObj<any>

const ControlCenterDemo = ({ controls }: { controls: Control[] }) => {
  const { useControlCenter } = AppleControlCenter
  const { open } = useControlCenter()

  useEffect(() => {
    setTimeout(() => open(), 100)
  }, [])

  return (
    <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600">
      <p className="text-white text-sm">Control Center appears in the top-right</p>
    </div>
  )
}

const basicControls: Control[] = [
  {
    id: 'wifi',
    title: 'Wi-Fi',
    subtitle: 'Home Network',
    icon: <Wifi />,
    size: '1x1',
    variant: 'primary',
    active: true,
    onPress: () => console.log('Wi-Fi toggled')
  },
  {
    id: 'bluetooth',
    title: 'Bluetooth',
    subtitle: 'On',
    icon: <Bluetooth />,
    size: '1x1',
    variant: 'primary',
    active: true,
    onPress: () => console.log('Bluetooth toggled')
  },
  {
    id: 'airplane',
    title: 'Airplane Mode',
    icon: <Plane />,
    size: '1x1',
    variant: 'default',
    active: false,
    onPress: () => console.log('Airplane mode toggled')
  },
  {
    id: 'flashlight',
    title: 'Flashlight',
    icon: <Flashlight />,
    size: '1x1',
    variant: 'default',
    active: false,
    onPress: () => console.log('Flashlight toggled')
  }
]

export const Default: Story = {
  render: () => (
    <AppleControlCenter.Provider controls={basicControls}>
      <ControlCenterDemo controls={basicControls} />
    </AppleControlCenter.Provider>
  )
}

const controlsWithSizes: Control[] = [
  {
    id: 'wifi',
    title: 'Wi-Fi',
    subtitle: 'Home Network',
    icon: <Wifi />,
    size: '1x1',
    variant: 'primary',
    active: true
  },
  {
    id: 'bluetooth',
    title: 'Bluetooth',
    subtitle: 'AirPods Pro',
    icon: <Bluetooth />,
    size: '1x1',
    variant: 'primary',
    active: true
  },
  {
    id: 'music',
    title: 'Now Playing',
    subtitle: 'Summer Breeze - Artist',
    icon: <Music />,
    size: '2x1',
    variant: 'default',
    active: true,
    actions: [
      {
        id: 'play',
        label: 'Play',
        icon: <Play />,
        onPress: () => console.log('Play')
      },
      {
        id: 'pause',
        label: 'Pause',
        icon: <Pause />,
        onPress: () => console.log('Pause')
      },
      {
        id: 'next',
        label: 'Next',
        icon: <SkipForward />,
        onPress: () => console.log('Next')
      },
      {
        id: 'previous',
        label: 'Previous',
        icon: <SkipBack />,
        onPress: () => console.log('Previous')
      }
    ]
  },
  {
    id: 'brightness',
    title: 'Brightness',
    icon: <Sun />,
    size: '1x2',
    variant: 'default',
    value: '75%'
  },
  {
    id: 'volume',
    title: 'Volume',
    icon: <Volume2 />,
    size: '1x2',
    variant: 'default',
    value: '60%'
  }
]

export const DifferentSizes: Story = {
  render: () => (
    <AppleControlCenter.Provider controls={controlsWithSizes}>
      <ControlCenterDemo controls={controlsWithSizes} />
    </AppleControlCenter.Provider>
  )
}

const controlsWithActions: Control[] = [
  {
    id: 'wifi',
    title: 'Wi-Fi',
    subtitle: 'Home Network',
    icon: <Wifi />,
    size: '1x1',
    variant: 'primary',
    active: true,
    actions: [
      {
        id: 'home',
        label: 'Home Network',
        onPress: () => console.log('Connect to Home')
      },
      {
        id: 'office',
        label: 'Office Network',
        onPress: () => console.log('Connect to Office')
      },
      {
        id: 'settings',
        label: 'Wi-Fi Settings',
        onPress: () => console.log('Open Settings')
      }
    ],
    onLongPress: () => console.log('Wi-Fi long pressed')
  },
  {
    id: 'bluetooth',
    title: 'Bluetooth',
    subtitle: 'AirPods Pro',
    icon: <Bluetooth />,
    size: '1x1',
    variant: 'primary',
    active: true,
    actions: [
      {
        id: 'airpods',
        label: 'AirPods Pro',
        onPress: () => console.log('Connect AirPods')
      },
      {
        id: 'speaker',
        label: 'HomePod',
        onPress: () => console.log('Connect HomePod')
      },
      {
        id: 'settings',
        label: 'Bluetooth Settings',
        onPress: () => console.log('Open Settings')
      }
    ],
    onLongPress: () => console.log('Bluetooth long pressed')
  },
  {
    id: 'camera',
    title: 'Camera',
    icon: <Camera />,
    size: '1x1',
    variant: 'default',
    actions: [
      {
        id: 'photo',
        label: 'Take Photo',
        icon: <Camera />,
        onPress: () => console.log('Take Photo')
      },
      {
        id: 'video',
        label: 'Record Video',
        onPress: () => console.log('Record Video')
      },
      {
        id: 'selfie',
        label: 'Selfie',
        onPress: () => console.log('Selfie Mode')
      }
    ],
    onLongPress: () => console.log('Camera long pressed')
  },
  {
    id: 'timer',
    title: 'Timer',
    icon: <Timer />,
    size: '1x1',
    variant: 'default',
    actions: [
      {
        id: '1min',
        label: '1 minute',
        onPress: () => console.log('1 min timer')
      },
      {
        id: '5min',
        label: '5 minutes',
        onPress: () => console.log('5 min timer')
      },
      {
        id: '10min',
        label: '10 minutes',
        onPress: () => console.log('10 min timer')
      },
      {
        id: 'custom',
        label: 'Custom',
        onPress: () => console.log('Custom timer')
      }
    ],
    onLongPress: () => console.log('Timer long pressed')
  }
]

export const WithLongPressActions: Story = {
  render: () => (
    <AppleControlCenter.Provider controls={controlsWithActions}>
      <ControlCenterDemo controls={controlsWithActions} />
    </AppleControlCenter.Provider>
  )
}

const allVariants: Control[] = [
  {
    id: 'default',
    title: 'Default',
    subtitle: 'Inactive',
    icon: <Lock />,
    size: '1x1',
    variant: 'default',
    active: false
  },
  {
    id: 'default-active',
    title: 'Default',
    subtitle: 'Active',
    icon: <Lock />,
    size: '1x1',
    variant: 'default',
    active: true
  },
  {
    id: 'primary',
    title: 'Primary',
    subtitle: 'Active',
    icon: <Wifi />,
    size: '1x1',
    variant: 'primary',
    active: true
  },
  {
    id: 'success',
    title: 'Success',
    subtitle: 'Active',
    icon: <Wifi />,
    size: '1x1',
    variant: 'success',
    active: true
  },
  {
    id: 'warning',
    title: 'Warning',
    subtitle: 'Active',
    icon: <Sun />,
    size: '1x1',
    variant: 'warning',
    active: true
  },
  {
    id: 'danger',
    title: 'Danger',
    subtitle: 'Active',
    icon: <Plane />,
    size: '1x1',
    variant: 'danger',
    active: true
  }
]

export const AllVariants: Story = {
  render: () => (
    <AppleControlCenter.Provider controls={allVariants}>
      <ControlCenterDemo controls={allVariants} />
    </AppleControlCenter.Provider>
  )
}

const largeControls: Control[] = [
  {
    id: 'music',
    title: 'Now Playing',
    subtitle: 'Summer Breeze - Artist Name',
    icon: <Music />,
    size: '2x2',
    variant: 'default',
    active: true,
    actions: [
      {
        id: 'play',
        label: 'Play',
        icon: <Play />,
        onPress: () => console.log('Play')
      },
      {
        id: 'pause',
        label: 'Pause',
        icon: <Pause />,
        onPress: () => console.log('Pause')
      }
    ]
  },
  {
    id: 'wifi',
    title: 'Wi-Fi',
    subtitle: 'Connected',
    icon: <Wifi />,
    size: '1x1',
    variant: 'primary',
    active: true
  },
  {
    id: 'bluetooth',
    title: 'Bluetooth',
    subtitle: 'On',
    icon: <Bluetooth />,
    size: '1x1',
    variant: 'primary',
    active: true
  }
]

export const LargeControls: Story = {
  render: () => (
    <AppleControlCenter.Provider controls={largeControls}>
      <ControlCenterDemo controls={largeControls} />
    </AppleControlCenter.Provider>
  )
}

const mixedLayout: Control[] = [
  {
    id: 'wifi',
    title: 'Wi-Fi',
    subtitle: 'Home',
    icon: <Wifi />,
    size: '1x1',
    variant: 'primary',
    active: true
  },
  {
    id: 'bluetooth',
    title: 'Bluetooth',
    subtitle: 'AirPods',
    icon: <Bluetooth />,
    size: '1x1',
    variant: 'primary',
    active: true
  },
  {
    id: 'brightness',
    title: 'Brightness',
    icon: <Sun />,
    size: '2x1',
    variant: 'default',
    value: '75%'
  },
  {
    id: 'airplane',
    title: 'Airplane',
    icon: <Plane />,
    size: '1x1',
    variant: 'default',
    active: false
  },
  {
    id: 'flashlight',
    title: 'Flashlight',
    icon: <Flashlight />,
    size: '1x1',
    variant: 'default',
    active: false
  },
  {
    id: 'volume',
    title: 'Volume',
    icon: <Volume2 />,
    size: '2x1',
    variant: 'default',
    value: '60%'
  },
  {
    id: 'camera',
    title: 'Camera',
    icon: <Camera />,
    size: '1x1',
    variant: 'default'
  },
  {
    id: 'calculator',
    title: 'Calculator',
    icon: <Calculator />,
    size: '1x1',
    variant: 'default'
  }
]

export const MixedLayout: Story = {
  render: () => (
    <AppleControlCenter.Provider controls={mixedLayout}>
      <ControlCenterDemo controls={mixedLayout} />
    </AppleControlCenter.Provider>
  )
}

const darkModeControl: Control[] = [
  {
    id: 'dark-mode',
    title: 'Dark Mode',
    subtitle: 'Enabled',
    icon: <Moon />,
    size: '1x1',
    variant: 'default',
    active: true,
    actions: [
      {
        id: 'light',
        label: 'Light Mode',
        icon: <Sun />,
        onPress: () => console.log('Light mode')
      },
      {
        id: 'dark',
        label: 'Dark Mode',
        icon: <Moon />,
        onPress: () => console.log('Dark mode')
      },
      {
        id: 'auto',
        label: 'Automatic',
        onPress: () => console.log('Auto mode')
      }
    ]
  },
  {
    id: 'wifi',
    title: 'Wi-Fi',
    icon: <Wifi />,
    size: '1x1',
    variant: 'primary',
    active: true
  },
  {
    id: 'bluetooth',
    title: 'Bluetooth',
    icon: <Bluetooth />,
    size: '1x1',
    variant: 'primary',
    active: true
  },
  {
    id: 'airplane',
    title: 'Airplane',
    icon: <Plane />,
    size: '1x1',
    variant: 'default',
    active: false
  }
]

export const DarkModeExample: Story = {
  render: () => (
    <AppleControlCenter.Provider controls={darkModeControl}>
      <ControlCenterDemo controls={darkModeControl} />
    </AppleControlCenter.Provider>
  )
}

const minimalControls: Control[] = [
  {
    id: 'wifi',
    title: 'Wi-Fi',
    icon: <Wifi />,
    size: '1x1',
    variant: 'primary',
    active: true
  },
  {
    id: 'bluetooth',
    title: 'Bluetooth',
    icon: <Bluetooth />,
    size: '1x1',
    variant: 'primary',
    active: true
  }
]

export const MinimalControls: Story = {
  render: () => (
    <AppleControlCenter.Provider controls={minimalControls}>
      <ControlCenterDemo controls={minimalControls} />
    </AppleControlCenter.Provider>
  )
}

const InteractiveDemo = () => {
  const { useControlCenter } = AppleControlCenter
  const { toggle, isOpen } = useControlCenter()

  return (
    <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-600">
      <button
        onClick={toggle}
        className="px-6 py-3 bg-white text-purple-600 font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all"
      >
        {isOpen ? 'Close' : 'Open'} Control Center
      </button>
    </div>
  )
}

export const Interactive: Story = {
  render: () => (
    <AppleControlCenter.Provider controls={mixedLayout}>
      <InteractiveDemo />
    </AppleControlCenter.Provider>
  )
}
