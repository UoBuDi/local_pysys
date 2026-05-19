/**
 * 图标预加载配置
 * 确保所有图标在离线模式下可用
 */

// 导入图标集（PurgeIcons 会自动检测并打包）
import '@iconify-json/mdi'
import '@iconify-json/ep'
import '@iconify-json/carbon'
import '@iconify-json/ant-design'
import '@iconify-json/zmdi'

export const iconSets = {
  mdi: 'Material Design Icons',
  ep: 'Element Plus Icons',
  carbon: 'Carbon Icons',
  'ant-design': 'Ant Design Icons',
  zmdi: 'ZMD Icons'
}

export default {
  iconSets
}
