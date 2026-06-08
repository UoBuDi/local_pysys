/**
 * 图标预加载配置
 * 使用 addCollection 将图标集数据注册到 @iconify/vue/offline 内存中
 * 供 <Icon> 组件运行时查找渲染，完全离线可用，不依赖任何在线API
 */
import { addCollection } from '@iconify/vue/offline'

// 导入图标集JSON数据
import epIcons from '@iconify-json/ep/icons.json'
import mdiIcons from '@iconify-json/mdi/icons.json'
import carbonIcons from '@iconify-json/carbon/icons.json'
import antDesignIcons from '@iconify-json/ant-design/icons.json'
import zmdiIcons from '@iconify-json/zmdi/icons.json'
import biIcons from '@iconify-json/bi/icons.json'
import radixIcons from '@iconify-json/radix-icons/icons.json'
import ionIcons from '@iconify-json/ion/icons.json'
import emojioneMonotoneIcons from '@iconify-json/emojione-monotone/icons.json'
import clarityIcons from '@iconify-json/clarity/icons.json'
import cibIcons from '@iconify-json/cib/icons.json'
import bxIcons from '@iconify-json/bx/icons.json'
import riIcons from '@iconify-json/ri/icons.json'
import icIcons from '@iconify-json/ic/icons.json'
import ciIcons from '@iconify-json/ci/icons.json'
import eosIcons from '@iconify-json/eos-icons/icons.json'

// 将图标集数据注册到内存，供 @iconify/vue 运行时查找
addCollection(epIcons)
addCollection(mdiIcons)
addCollection(carbonIcons)
addCollection(antDesignIcons)
addCollection(zmdiIcons)
addCollection(biIcons)
addCollection(radixIcons)
addCollection(ionIcons)
addCollection(emojioneMonotoneIcons)
addCollection(clarityIcons)
addCollection(cibIcons)
addCollection(bxIcons)
addCollection(riIcons)
addCollection(icIcons)
addCollection(ciIcons)
addCollection(eosIcons)
