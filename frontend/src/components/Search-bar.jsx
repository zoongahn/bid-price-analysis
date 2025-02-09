import {Fragment, useState} from "react"
import {FaMagnifyingGlass} from "react-icons/fa6" // 돋보기 아이콘
import {Listbox, Transition} from "@headlessui/react"
import {CheckIcon, ChevronUpDownIcon} from "@heroicons/react/20/solid"

const SearchBar = ({dropdownOptions, onSearch}) => {
	const [selected, setSelected] = useState(dropdownOptions[0])
	const [query, setQuery] = useState("")

	const handleSubmit = (e) => {
		e.preventDefault()
		onSearch({selectedOption: selected, queryValue: query})

	}

	return (
		<form onSubmit={handleSubmit} className="flex items-center border-none rounded-lg w-full h-12 bg-white px-20">
			{/* 드롭다운메뉴 */}
			<div className="relative min-w-[200px]">
				<Listbox value={selected} onChange={setSelected}>
					<div className="relative">
						<Listbox.Button
							className="w-full cursor-pointer rounded-lg bg-white py-3 px-4 text-left text-md shadow-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500">
							<span className="block truncate">{selected}</span>
							<span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
								<ChevronUpDownIcon className="h-5 w-5 text-gray-500" aria-hidden="true"/>
							</span>
						</Listbox.Button>
						<Transition
							as={Fragment}
							leave="transition ease-in duration-100"
							leaveFrom="opacity-100"
							leaveTo="opacity-0"
						>
							<Listbox.Options
								className="absolute z-10 top-full left-0 mt-1 max-h-60 w-full overflow-visible rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-md">
								{/* eslint-disable-next-line react/prop-types */}
								{dropdownOptions.map((option, optionIdx) => (
									<Listbox.Option
										key={optionIdx}
										className={({active}) =>
											`relative cursor-pointer select-none py-2 pl-10 pr-4 ${
												active ? "bg-amber-100 text-amber-900" : "text-gray-900"
											}`
										}
										value={option}
									>
										{({selected}) => (
											<>
												<span
													className={`block truncate ${
														selected ? "font-medium" : "font-normal"
													}`}
												>
													{option}
												</span>
												{selected ? (
													<span
														className="absolute inset-y-0 left-0 flex items-center pl-3 text-amber-600">
														<CheckIcon className="h-5 w-5" aria-hidden="true"/>
													</span>
												) : null}
											</>
										)}
									</Listbox.Option>
								))}
							</Listbox.Options>
						</Transition>
					</div>
				</Listbox>
			</div>

			{/* 입력 필드 */}
			<input
				type="text"
				value={query}
				onChange={(e) => setQuery(e.target.value)}
				className="flex-1 mx-3 text-4xl border-b-2 border-gray-500 mt-2 focus:outline-none focus:ring-0"
			/>

			{/* 검색 버튼 */}
			<button type="submit" className="cursor-pointer">
				<FaMagnifyingGlass size="20"/>
			</button>
		</form>
	)
}

export default SearchBar
